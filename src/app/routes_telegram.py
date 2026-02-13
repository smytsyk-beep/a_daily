# src/app/routes_telegram.py

from __future__ import annotations

from datetime import date, datetime
import time
from typing import Any, Dict, Optional


from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, repo
from app.modules import daily_digest as daily_digest_module
from app.telegram_client import send_message
from app.telegram_prefs import get_telegram_prefs_from_user
from app.repo import session_scope
from app.i18n import tr, normalize_locale
from app.birth_geo_service import ensure_birthdata_geo_for_user

from common.plans import (
    PlanFeature,
    feature_title_key,
    get_plan_runtime_config,
    get_user_plan,
    plan_title_key,
)

from common.runtime_cache import RateLimiter, TTLCache


router = APIRouter(tags=["telegram"], prefix="/telegram")

# Ключ и значения состояний онбординга в user.prefs
ONBOARDING_STATE_KEY = "onboarding_state"

STATE_COMPLETE = "complete"
STATE_AGE_GATE = "age_gate_pending"
STATE_ASK_BIRTH_DATE = "ask_birth_date"
STATE_ASK_BIRTH_TIME = "ask_birth_time"
STATE_ASK_BIRTH_PLACE = "ask_birth_place"
STATE_ASK_PREFS_TOPICS = "ask_prefs_topics"
STATE_ASK_PREFS_DELIVERY = "ask_prefs_delivery"


# ---------- Anti-spam (MVP) + Cache ----------

TODAY_LIMITER = RateLimiter(max_calls=2, window_seconds=60)  # 2/min
UPGRADE_LIMITER = RateLimiter(max_calls=3, window_seconds=60)  # 3/min

# Кэшируем готовый текст /today на (примерно) сутки.
TODAY_CACHE = TTLCache[str](ttl_seconds=26 * 60 * 60, max_items=50_000)


def _cache_key_today(user_id: int, day: date, locale: str, digest_cap: str) -> str:
    return f"tg:today:{user_id}:{day.isoformat()}:{locale}:{digest_cap}"


# ---------- Вспомогательные функции ----------


def _safe_prefs_dict(user: models.User) -> Dict[str, Any]:
    raw = getattr(user, "prefs", None)
    if not isinstance(raw, dict):
        return {}
    return dict(raw)


def _get_onboarding_state(user: models.User) -> Optional[str]:
    prefs = _safe_prefs_dict(user)
    return prefs.get(ONBOARDING_STATE_KEY)


def _set_onboarding_state(user: models.User, state: Optional[str]) -> Dict[str, Any]:
    prefs = _safe_prefs_dict(user)

    if state is None:
        prefs.pop(ONBOARDING_STATE_KEY, None)
    else:
        prefs[ONBOARDING_STATE_KEY] = state

    user.prefs = prefs
    return prefs


def _get_user_prefs(user: models.User) -> Dict[str, Any]:
    return _safe_prefs_dict(user)


def _save_user_prefs(db: Session, user: models.User, prefs: Dict[str, Any]) -> None:
    user.prefs = prefs
    db.add(user)
    db.commit()
    db.refresh(user)


def _get_or_create_user_by_tg_id(
    db: Session,
    tg_user_id: int,
    username: Optional[str],
    language_code: Optional[str],
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> models.User:
    tg_str = str(tg_user_id)
    normalized = normalize_locale(language_code)

    def _build_display_name() -> Optional[str]:
        parts: list[str] = []
        if first_name:
            parts.append(first_name)
        if last_name:
            parts.append(last_name)
        display = " ".join(parts).strip()
        if not display:
            display = username or None
        return display

    user = db.query(models.User).filter(models.User.tg_user_id == tg_str).first()
    if user:
        prefs = _safe_prefs_dict(user)
        changed = False

        # Автообновление locale, если юзер сам не фиксировал язык
        if not prefs.get("locale_manual"):
            if user.locale in (None, "", "en") and normalized != user.locale:
                user.locale = normalized
                changed = True

        # Обновляем display_name, если он пустой или технический user_<id>
        current_name = getattr(user, "display_name", None)
        candidate = _build_display_name()
        if candidate and (not current_name or current_name == f"user_{user.id}"):
            user.display_name = candidate
            changed = True

        if changed:
            db.commit()
            db.refresh(user)

        return user

    # Новый пользователь
    user = models.User(
        tg_user_id=tg_str,
        locale=normalized,
        display_name=_build_display_name(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def _extract_message(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "message" in update:
        return update["message"]

    if "callback_query" in update:
        cq = update["callback_query"]
        msg = cq.get("message") or {}
        msg["from"] = cq.get("from") or {}
        msg["_callback_data"] = cq.get("data")
        return msg

    return None


def _handle_onboarding_text_message(
    db: Session,
    user: models.User,
    chat_id: int,
    text: str,
) -> None:
    prefs = _get_user_prefs(user)
    state = prefs.get(ONBOARDING_STATE_KEY)
    text = (text or "").strip()
    lang = user.locale

    print(
        f"[TG] _handle_onboarding_text_message: user_id={user.id}, "
        f"state={state!r}, text={text!r}, prefs={prefs}"
    )

    if not state or state == STATE_COMPLETE:
        send_message(chat_id, tr(lang, "tg.help.basic"))
        return

    # --- Шаг 1: дата рождения ---
    if state == STATE_ASK_BIRTH_DATE:
        try:
            bdate = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.birth_date_invalid"),
                parse_mode="Markdown",
            )
            return

        prefs["birth_date"] = bdate.isoformat()
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_BIRTH_TIME
        _save_user_prefs(db, user, prefs)

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.birth_time_prompt"),
            parse_mode="Markdown",
        )
        return

    # --- Шаг 2: время рождения ---
    if state == STATE_ASK_BIRTH_TIME:
        lowered = text.lower()
        if lowered in {
            "не знаю",
            "не помню",
            "не помню точно",
            "dont know",
            "don't know",
            "not sure",
            "no se",
            "no sé",
        }:
            hh, mm = 12, 0
        else:
            try:
                t = datetime.strptime(text, "%H:%M").time()
            except ValueError:
                send_message(
                    chat_id,
                    tr(lang, "tg.onboarding.birth_time_invalid"),
                    parse_mode="Markdown",
                )
                return
            hh, mm = t.hour, t.minute

        prefs["birth_time"] = f"{hh:02d}:{mm:02d}"
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_BIRTH_PLACE
        _save_user_prefs(db, user, prefs)

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.birth_place_prompt"),
            parse_mode="Markdown",
        )
        return

    # --- Шаг 3: место рождения + запись BirthData ---
    if state == STATE_ASK_BIRTH_PLACE:
        if not text:
            print("[TG] Empty birth place")
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.birth_place_empty"),
                parse_mode="Markdown",
            )
            return

        prefs["birth_place"] = text
        _save_user_prefs(db, user, prefs)
        print(f"[TG] Birth place saved: {text!r}")

        birth_date_str = prefs.get("birth_date")
        birth_time_str = prefs.get("birth_time") or "12:00"

        try:
            bdate = (
                datetime.fromisoformat(birth_date_str).date()
                if birth_date_str
                else None
            )
        except Exception:
            print(
                "[TG] Failed to parse birth_date from prefs, skipping BirthData insert"
            )
            bdate = None

        if bdate:
            print(
                f"[TG] Upserting BirthData for user_id={user.id}, "
                f"date={bdate}, time={birth_time_str}, place={text!r}"
            )
            # ВАЖНО: используем внутренний PK пользователя, а не tg_user_id.
            repo.upsert_birth_data(
                db,
                user_ref=str(user.id),
                birth_date=bdate,
                birth_time=birth_time_str,
                place=text,
                lat=None,
                lon=None,
                tz=None,
            )

            # После сохранения BirthData пробуем резолвить lat/lon/tz
            ensure_birthdata_geo_for_user(db, user)

        # После базовых данных переходим к предпочтениям по темам
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_PREFS_TOPICS
        _save_user_prefs(db, user, prefs)
        print(
            f"[TG] Birth data saved, asking prefs topics for user_id={user.id}, "
            f"state={STATE_ASK_PREFS_TOPICS!r}"
        )

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.prefs_topics_prompt"),
            parse_mode="Markdown",
        )
        return

    # --- Шаг 4: предпочтения по темам дайджеста ---
    if state == STATE_ASK_PREFS_TOPICS:
        # Ожидаем числа 1–4, можно через запятую или пробел
        digits = {ch for ch in text if ch in "1234"}
        if not digits:
            print(f"[TG] Invalid prefs topics input: {text!r}")
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.prefs_topics_invalid"),
                parse_mode="Markdown",
            )
            return

        mapping = {
            "1": "work",
            "2": "relationships",
            "3": "money",
            "4": "selfcare",
        }
        topics = sorted({mapping[d] for d in digits})
        print(f"[TG] Parsed prefs topics for user_id={user.id}: {topics}")

        prefs["digest_interests"] = topics
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_PREFS_DELIVERY
        _save_user_prefs(db, user, prefs)

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.prefs_delivery_prompt"),
            parse_mode="Markdown",
        )
        return

    # --- Шаг 5: длина дайджеста + запись колонок и display_name ---
    if state == STATE_ASK_PREFS_DELIVERY:
        normalized = text.lower().strip()

        length_code: Optional[str] = None
        if normalized.startswith("1"):
            length_code = "short"
        elif normalized.startswith("2"):
            length_code = "medium"
        elif normalized.startswith("3"):
            length_code = "long"
        elif "short" in normalized:
            length_code = "short"
        elif "medium" in normalized:
            length_code = "medium"
        elif "long" in normalized:
            length_code = "long"

        if not length_code:
            print(f"[TG] Invalid prefs delivery input: {text!r}")
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.prefs_delivery_invalid"),
                parse_mode="Markdown",
            )
            return

        print(
            f"[TG] Parsed digest_length_preference for user_id={user.id}: "
            f"{length_code!r}"
        )

        # Сохраняем в prefs + помечаем онбординг как завершённый
        prefs["digest_length_preference"] = length_code
        prefs[ONBOARDING_STATE_KEY] = STATE_COMPLETE
        _save_user_prefs(db, user, prefs)

        # Дублируем в отдельные колонки, если они есть на модели
        interests = prefs.get("digest_interests")

        if hasattr(user, "digest_length_preference"):
            try:
                user.digest_length_preference = length_code  # type: ignore[assignment]
            except Exception as e:
                print(f"[TG] Failed to set user.digest_length_preference: {e!r}")

        if hasattr(user, "digest_interests") and interests is not None:
            try:
                user.digest_interests = interests  # type: ignore[assignment]
            except Exception as e:
                print(f"[TG] Failed to set user.digest_interests: {e!r}")

        # Заполняем display_name, если он ещё пустой
        if hasattr(user, "display_name"):
            try:
                if not user.display_name:
                    name_parts: list[str] = []
                    first_name = getattr(user, "first_name", None)
                    last_name = getattr(user, "last_name", None)
                    username = getattr(user, "username", None)

                    if first_name:
                        name_parts.append(first_name)
                    if last_name:
                        name_parts.append(last_name)

                    if name_parts:
                        user.display_name = " ".join(name_parts)  # type: ignore[assignment]
                    elif username:
                        user.display_name = username  # type: ignore[assignment]
                    else:
                        user.display_name = f"user_{user.id}"  # type: ignore[assignment]

                    print(
                        f"[TG] display_name set for user_id={user.id}: "
                        f"{user.display_name!r}"
                    )
            except Exception as e:
                print(f"[TG] Failed to set user.display_name: {e!r}")

        # Фиксируем все изменения user в БД
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"[TG] Onboarding complete for user_id={user.id}")

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.complete"),
            parse_mode="Markdown",
        )
        return

    # На всякий случай: неизвестное состояние → сбрасываем.
    print(f"[TG] Unknown onboarding state inside handler: {state!r}, resetting")
    prefs.pop(ONBOARDING_STATE_KEY, None)
    _save_user_prefs(db, user, prefs)
    send_message(
        chat_id,
        tr(lang, "tg.help.basic"),
        parse_mode="Markdown",
    )


def _get_user_plan_for_db(db: Session, user: models.User) -> tuple[str, object]:
    """
    Возвращаем:
      - plan_code (строка: demo/daily/full/internal)
      - plan_cfg (PlanRuntimeConfig)
    """
    plan_code = get_user_plan(db, user.id)
    plan_cfg = get_plan_runtime_config(plan_code)
    return plan_code, plan_cfg


# ---------- Основной webhook ----------


@router.post("/webhook", status_code=200)
async def telegram_webhook(request: Request) -> Dict[str, str]:
    update = await request.json()
    print(f"[TG] Incoming update: {update}")

    message = _extract_message(update)
    if not message:

        return {"status": "ignored"}

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="chat_id missing"
        )

    text: str = (message.get("text") or "").strip()
    callback_data: Optional[str] = message.get("_callback_data")

    from_user = message.get("from") or {}
    tg_user_id = from_user.get("id")
    username = from_user.get("username")
    language_code = from_user.get("language_code")
    first_name = from_user.get("first_name")
    last_name = from_user.get("last_name")

    if tg_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="from.id missing"
        )

    with session_scope() as db:
        user = _get_or_create_user_by_tg_id(
            db,
            tg_user_id=tg_user_id,
            username=username,
            language_code=language_code,
            first_name=first_name,
            last_name=last_name,
        )

        onboarding_state = _get_onboarding_state(user)
        tg_prefs = get_telegram_prefs_from_user(user)
        lang = user.locale

        # ========== 0. CALLBACK-ветка ==========

        if callback_data:

            # 0. Age gate
            if callback_data == "age_yes":
                now = datetime.utcnow()
                user.age_gate_accepted_at = now
                user.disclaimer_accepted_at = now
                user.birthdata_consent_at = now

                _set_onboarding_state(user, STATE_ASK_BIRTH_DATE)
                db.commit()

                send_message(
                    chat_id=chat_id,
                    text=tr(user.locale or "en", "tg.age_gate.accepted"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            if callback_data == "age_no":
                _set_onboarding_state(user, None)
                db.commit()

                send_message(
                    chat_id=chat_id,
                    text=tr(user.locale or "en", "tg.age_gate.declined"),
                )
                return {"status": "ok"}

            lang_code = user.locale or "en"

            # 1. Settings: язык
            if callback_data == "settings_lang":
                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": tr(lang_code, "tg.settings.lang.en"),
                                "callback_data": "settings_lang_en",
                            },
                            {
                                "text": tr(lang_code, "tg.settings.lang.ru"),
                                "callback_data": "settings_lang_ru",
                            },
                            {
                                "text": tr(lang_code, "tg.settings.lang.es"),
                                "callback_data": "settings_lang_es",
                            },
                        ]
                    ]
                }
                send_message(
                    chat_id=chat_id,
                    text=tr(lang_code, "tg.settings.language.choose"),
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                return {"status": "ok"}

            if callback_data.startswith("settings_lang_"):
                new_lang = callback_data.split("settings_lang_", 1)[1]
                if new_lang not in ("en", "ru", "es"):
                    new_lang = "en"

                prefs = _get_user_prefs(user)
                prefs["locale_manual"] = True
                user.locale = new_lang
                _save_user_prefs(db, user, prefs)

                lang_label = tr(new_lang, f"tg.settings.lang.{new_lang}")
                msg = tr(new_lang, "tg.settings.language.changed", language=lang_label)
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 2. Settings: часовой пояс
            if callback_data == "settings_tz":
                tz_keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Europe/Kyiv",
                                "callback_data": "settings_tz_Europe/Kyiv",
                            },
                            {
                                "text": "Europe/Bucharest",
                                "callback_data": "settings_tz_Europe/Bucharest",
                            },
                        ],
                        [
                            {
                                "text": "Europe/Istanbul",
                                "callback_data": "settings_tz_Europe/Istanbul",
                            },
                            {
                                "text": "UTC",
                                "callback_data": "settings_tz_UTC",
                            },
                        ],
                    ]
                }
                send_message(
                    chat_id=chat_id,
                    text=tr(lang_code, "tg.settings.timezone.choose"),
                    parse_mode="Markdown",
                    reply_markup=tz_keyboard,
                )
                return {"status": "ok"}

            if callback_data.startswith("settings_tz_"):
                tz = callback_data.split("settings_tz_", 1)[1]

                prefs = _get_user_prefs(user)
                prefs["timezone"] = tz
                user.timezone = tz
                _save_user_prefs(db, user, prefs)

                msg = tr(lang_code, "tg.settings.timezone.changed", timezone=tz)
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 3. Settings: время доставки
            if callback_data == "settings_time":
                time_keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "07:00",
                                "callback_data": "settings_time_07:00",
                            },
                            {
                                "text": "09:00",
                                "callback_data": "settings_time_09:00",
                            },
                        ],
                        [
                            {
                                "text": "12:00",
                                "callback_data": "settings_time_12:00",
                            },
                            {
                                "text": "18:00",
                                "callback_data": "settings_time_18:00",
                            },
                        ],
                    ]
                }
                send_message(
                    chat_id=chat_id,
                    text=tr(lang_code, "tg.settings.delivery_time.choose"),
                    parse_mode="Markdown",
                    reply_markup=time_keyboard,
                )
                return {"status": "ok"}

            if callback_data.startswith("settings_time_"):
                time_str = callback_data.split("settings_time_", 1)[1]
                try:
                    t_obj = datetime.strptime(time_str, "%H:%M").time()
                except ValueError:
                    t_obj = None

                prefs = _get_user_prefs(user)
                prefs["delivery_time_local"] = time_str
                if t_obj is not None:
                    user.delivery_time_local = t_obj
                else:
                    # на всякий случай, если модель позволяет хранить строку
                    user.delivery_time_local = time_str  # type: ignore[attr-defined]
                _save_user_prefs(db, user, prefs)

                msg = tr(
                    lang_code,
                    "tg.settings.delivery_time.changed",
                    delivery_time=time_str,
                )
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 4. Feedback по дайджесту
            if callback_data == "dd_like":
                ack = tr(lang_code, "tg.feedback.like_ack")

            elif callback_data == "dd_dislike":
                ack = tr(lang_code, "tg.feedback.dislike_ack")

            elif callback_data == "dd_hide":
                ack = tr(lang_code, "tg.feedback.hide_ack")

            else:
                ack = tr(lang_code, "tg.feedback.generic_ack")

            send_message(chat_id=chat_id, text=ack)
            return {"status": "ok"}

        # ========== 1. /start ==========

        if text.startswith("/start"):

            if not user.age_gate_accepted_at:
                if user.delivery_enabled is not True:
                    user.delivery_enabled = True

                _set_onboarding_state(user, STATE_AGE_GATE)

                msg = tr(lang, "tg.age_gate.question")
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {
                                "text": tr(lang, "tg.age_gate.yes_btn"),
                                "callback_data": "age_yes",
                            },
                            {
                                "text": tr(lang, "tg.age_gate.no_btn"),
                                "callback_data": "age_no",
                            },
                        ]
                    ]
                }

                db.commit()
                send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                return {"status": "ok"}

            prefs = _safe_prefs_dict(user)
            has_birth_data = all(
                key in prefs for key in ("birth_date", "birth_time", "birth_place")
            )

            if not has_birth_data:
                _set_onboarding_state(user, STATE_ASK_BIRTH_DATE)
                db.commit()
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.start.ask_birth_date"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            _set_onboarding_state(user, STATE_COMPLETE)

            if user.delivery_enabled is not True:
                user.delivery_enabled = True

            db.commit()

            send_message(
                chat_id=chat_id,
                text=tr(lang, "tg.start.welcome", bot_name="AstroDaily"),
                parse_mode="Markdown",
            )
            return {"status": "ok"}

        # ========= 4. /today =========

        if text.startswith("/today"):
            # rate limit
            rl = TODAY_LIMITER.check(f"today:{user.id}")
            if not rl.allowed:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.rate_limit", seconds=rl.retry_after_seconds),
                )
                return {"status": "ok"}

            today = date.today()

            # План пользователя и базовое ограничение длины
            plan_code, plan_cfg = _get_user_plan_for_db(db, user)
            digest_cap = plan_cfg.digest_cap  # "short" / "medium" / "long"

            # Предпочтительная длина из профиля пользователя
            length_pref = None

            # 1) сначала колонка users.digest_length_preference
            if getattr(user, "digest_length_preference", None):
                length_pref = user.digest_length_preference

            # 2) если пусто — пробуем prefs JSONB
            if not length_pref and getattr(user, "prefs", None):
                prefs = user.prefs or {}
                if isinstance(prefs, dict):
                    length_pref = prefs.get("digest_length_preference")

            # 3) если всё ещё ничего или странное значение — берём плановую длину
            if length_pref not in ("short", "medium", "long"):
                length_pref = digest_cap

            # Конфиг для модуля дайджеста
            digest_config: dict[str, object] = {
                "time_local": tg_prefs.time_local,
                "length": length_pref,
            }

            # Ключ кэша можно оставлять как раньше, чтобы сильно не трогать логику
            cache_key = _cache_key_today(user.id, today, lang, length_pref)
            cached = TODAY_CACHE.get(cache_key)
            if cached:
                send_message(
                    chat_id=chat_id,
                    text=cached,
                    parse_mode="Markdown",
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {
                                    "text": tr(lang, "tg.feedback.like_btn"),
                                    "callback_data": "dd_like",
                                },
                                {
                                    "text": tr(lang, "tg.feedback.dislike_btn"),
                                    "callback_data": "dd_dislike",
                                },
                                {
                                    "text": tr(lang, "tg.feedback.hide_btn"),
                                    "callback_data": "dd_hide",
                                },
                            ]
                        ]
                    },
                )
                return {"status": "ok"}

            try:
                atoms = daily_digest_module.compute(
                    user_id=user.id,
                    config=digest_config,
                )
            except Exception as exc:
                print(f"[TG] /today error for user_id={user.id}: {exc!r}")
                send_message(chat_id=chat_id, text=tr(lang, "tg.today.failed"))
                return {"status": "ok"}

            if not atoms:
                send_message(chat_id=chat_id, text=tr(lang, "tg.today.failed"))
                return {"status": "ok"}

            atom = atoms[0]
            title = atom.get("title") or "Your daily digest"
            body = atom.get("body") or ""
            affirmation = atom.get("affirmation")

            lines = [f"✨ *{title}* ✨", "", str(body)]
            if affirmation:
                label = tr(lang, "tg.today.affirmation_label")
                lines.extend(["", f"_{label}_ {affirmation}"])

            full_text = "\n".join(lines)

            reply_markup = {
                "inline_keyboard": [
                    [
                        {
                            "text": tr(lang, "tg.feedback.like_btn"),
                            "callback_data": "dd_like",
                        },
                        {
                            "text": tr(lang, "tg.feedback.dislike_btn"),
                            "callback_data": "dd_dislike",
                        },
                        {
                            "text": tr(lang, "tg.feedback.hide_btn"),
                            "callback_data": "dd_hide",
                        },
                    ]
                ]
            }

            TODAY_CACHE.set(cache_key, full_text)

            send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
            return {"status": "ok"}

        # ========== 3. /snooze ==========

        if text.startswith("/snooze"):

            if user.delivery_enabled is None or user.delivery_enabled:
                user.delivery_enabled = False
                msg = tr(lang, "tg.snooze.paused")
            else:
                user.delivery_enabled = True
                msg = tr(lang, "tg.snooze.resumed")

            db.commit()
            send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

            return {"status": "ok"}

        # ========== 4. /plan ==========

        if text.startswith("/plan"):
            plan_code, plan_cfg = _get_user_plan_for_db(db, user)
            plan_name = tr(lang, plan_title_key(plan_code))

            # список фич
            feat_lines = []
            for f in plan_cfg.features:
                feat_lines.append(f"• {tr(lang, feature_title_key(f))}")
            features_block = "\n".join(feat_lines) if feat_lines else "• —"

            msg = (
                tr(lang, "tg.plan.current", plan_name=plan_name)
                + "\n\n"
                + tr(lang, "tg.plan.features", features=features_block)
                + "\n\n"
                + tr(lang, "tg.plan.upgrade_hint")
            )

            send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            return {"status": "ok"}

        # ========== 5. /upgrade ==========

        if text.startswith("/upgrade"):
            print(f"[TG] Handling /upgrade for user_id={user.id}")

            lang = user.locale or "en"

            # Берём фактический план пользователя (с учётом entitlements)
            plan_code = get_user_plan(db, user.id)

            if plan_code in ("full", "internal"):
                i18n_key = "tg.upgrade.already_full"
            else:
                i18n_key = "tg.upgrade.summary"

            plan_name = tr(lang, plan_title_key(plan_code))
            msg = tr(lang, i18n_key, plan_name=plan_name)

            send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="Markdown",
            )
            return {"status": "ok"}

        # ========== 6. /settings ==========

        if text.startswith("/settings"):
            lang_code = user.locale or "en"

            # Текущий план
            plan_code, plan_cfg = _get_user_plan_for_db(db, user)
            plan_name = tr(lang_code, plan_title_key(plan_code))

            # Читаем язык (человеко-понятное имя)
            lang_label = tr(lang_code, f"tg.settings.lang.{lang_code}")

            # Часовой пояс
            tz_value = getattr(user, "timezone", None)
            if not tz_value:
                timezone_label = tr(lang_code, "tg.settings.timezone.not_set")
            else:
                timezone_label = str(tz_value)

            # Время дайджеста
            dt_value = getattr(user, "delivery_time_local", None)
            if dt_value:
                if hasattr(dt_value, "strftime"):
                    delivery_time_label = dt_value.strftime("%H:%M")
                else:
                    delivery_time_label = str(dt_value)
            else:
                delivery_time_label = tr(lang_code, "tg.settings.delivery_time.not_set")

            # Статус доставки (snooze)
            delivery_enabled = getattr(user, "delivery_enabled", True)
            delivery_status_key = (
                "tg.settings.delivery.enabled"
                if delivery_enabled
                else "tg.settings.delivery.disabled"
            )
            delivery_status = tr(lang_code, delivery_status_key)

            msg = tr(
                lang_code,
                "tg.settings.summary",
                language=lang_label,
                plan_name=plan_name,
                timezone=timezone_label,
                delivery_time=delivery_time_label,
                delivery_status=delivery_status,
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.language"),
                            "callback_data": "settings_lang",
                        },
                        {
                            "text": tr(lang_code, "tg.settings.btn.timezone"),
                            "callback_data": "settings_tz",
                        },
                    ],
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.delivery_time"),
                            "callback_data": "settings_time",
                        }
                    ],
                ]
            }

            send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            return {"status": "ok"}

        # ========== 7. /help ==========

        if text.startswith("/help"):
            lang = user.locale or "en"

            msg = tr(lang, "tg.help.full")
            send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="Markdown",
            )
            return {"status": "ok"}

        # ========== 8. Незавершённый онбординг ==========

        if (
            onboarding_state
            and onboarding_state != STATE_COMPLETE
            and not text.startswith("/")
        ):
            _handle_onboarding_text_message(db, user, chat_id, text)
            return {"status": "ok"}

        # ========== 9. Help по умолчанию ==========

        send_message(chat_id=chat_id, text=tr(lang, "tg.help.basic"))
        return {"status": "ok"}
