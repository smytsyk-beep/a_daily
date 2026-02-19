# src/app/routes_telegram.py

from __future__ import annotations

from datetime import date, datetime
import time
from typing import Any, Dict, Optional


from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, repo
from app.modules import daily_digest as daily_digest_module
from app.telegram_client import send_message, answer_callback_query
from app.telegram_prefs import get_telegram_prefs_from_user
from app.repo import session_scope
from app.i18n import tr, normalize_locale
from app.birth_geo_service import ensure_birthdata_geo_for_user
from app.services.timezone import tz_by_latlon

from common.plans import (
    PlanFeature,
    feature_title_key,
    get_plan_runtime_config,
    get_user_plan,
    plan_title_key,
)

from common.runtime_cache import RateLimiter, TTLCache
from common.logging import logger


router = APIRouter(tags=["telegram"], prefix="/telegram")

# Ключ и значения состояний онбординга в user.prefs
ONBOARDING_STATE_KEY = "onboarding_state"
SETTINGS_EDIT_STATE_KEY = "settings_edit_state"

STATE_COMPLETE = "complete"
STATE_AGE_GATE = "age_gate_pending"
STATE_ASK_BIRTH_DATE = "ask_birth_date"
STATE_ASK_BIRTH_TIME = "ask_birth_time"
STATE_ASK_BIRTH_PLACE = "ask_birth_place"
STATE_ASK_TIMEZONE_LOCATION = "ask_timezone_location"
STATE_ASK_PREFS_TOPICS = "ask_prefs_topics"
STATE_ASK_PREFS_DELIVERY = "ask_prefs_delivery"

# Settings edit states
STATE_EDIT_BIRTH_DATE = "edit_birth_date"
STATE_EDIT_BIRTH_TIME = "edit_birth_time"
STATE_EDIT_BIRTH_PLACE = "edit_birth_place"


# ---------- Anti-spam (MVP) + Cache ----------

TODAY_LIMITER = RateLimiter(max_calls=2, window_seconds=60)  # 2/min
UPGRADE_LIMITER = RateLimiter(max_calls=3, window_seconds=60)  # 3/min

# Уровень 1 кэширования: готовый текст /today (user_id + day + locale + digest_cap + interests).
# TTL ~26 ч. При смене интересов ключ меняется — дайджест пересчитывается.
TODAY_CACHE = TTLCache[str](ttl_seconds=26 * 60 * 60, max_items=50_000)


def _cache_key_today(
    user_id: int, day: date, locale: str, digest_cap: str, interests: list[str]
) -> str:
    interests_part = ",".join(sorted(interests)) if interests else "general"
    return (
        f"tg:today:{user_id}:{day.isoformat()}:{locale}:{digest_cap}:{interests_part}"
    )


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
        msg["_callback_query_id"] = cq.get("id")  # Извлекаем ID для answerCallbackQuery
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

    logger.info(
        "Handling onboarding text message",
        user_id=user.id,
        state=state,
        text_length=len(text),
        prefs=prefs,
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
            logger.warning("Empty birth place received", user_id=user.id)
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.birth_place_empty"),
                parse_mode="Markdown",
            )
            return

        prefs["birth_place"] = text
        _save_user_prefs(db, user, prefs)
        logger.info("Birth place saved", user_id=user.id, place=text)

        birth_date_str = prefs.get("birth_date")
        birth_time_str = prefs.get("birth_time") or "12:00"

        try:
            bdate = (
                datetime.fromisoformat(birth_date_str).date()
                if birth_date_str
                else None
            )
        except Exception:
            logger.warning(
                "Failed to parse birth_date from prefs",
                user_id=user.id,
                birth_date_str=birth_date_str,
            )
            bdate = None

        if bdate:
            logger.info(
                "Upserting BirthData",
                user_id=user.id,
                date=str(bdate),
                time=birth_time_str,
                place=text,
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

        # После базовых данных переходим к запросу геолокации для timezone
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_TIMEZONE_LOCATION
        _save_user_prefs(db, user, prefs)
        logger.info(
            "Birth data saved, moving to timezone location request",
            user_id=user.id,
            state=STATE_ASK_TIMEZONE_LOCATION,
        )

        # Отправить сообщение с кнопкой запроса геолокации
        reply_markup = {
            "keyboard": [
                [
                    {
                        "text": tr(lang, "tg.onboarding.timezone_location_btn"),
                        "request_location": True,
                    }
                ],
                [
                    {
                        "text": tr(lang, "tg.onboarding.timezone_location_skip"),
                    }
                ],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.timezone_location_prompt"),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        return

    # --- Шаг 3.5: обработка пропуска геолокации ---
    if state == STATE_ASK_TIMEZONE_LOCATION:
        # Если пользователь написал "Пропустить" или любой другой текст
        # (не location message), пропускаем и используем timezone из birth_place
        logger.info(
            "User skipped timezone location request",
            user_id=user.id,
        )

        # КРИТИЧНО: Резолвим timezone из birth_place через BirthData
        ensure_birthdata_geo_for_user(db, user)

        # Берём timezone из BirthData и устанавливаем в user.timezone
        birth_data = (
            db.query(models.BirthData)
            .filter(models.BirthData.user_id == user.id)
            .order_by(models.BirthData.id.desc())
            .first()
        )

        if birth_data and birth_data.tz:
            user.timezone = birth_data.tz
            prefs["timezone"] = birth_data.tz
            logger.info(
                "Timezone set from birth place",
                user_id=user.id,
                timezone=birth_data.tz,
            )
        else:
            # Fallback: если не удалось определить timezone, используем UTC
            user.timezone = "UTC"
            prefs["timezone"] = "UTC"
            logger.warning(
                "Could not determine timezone from birth place, using UTC",
                user_id=user.id,
            )

        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_PREFS_TOPICS
        _save_user_prefs(db, user, prefs)

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.prefs_topics_prompt"),
            parse_mode="Markdown",
            reply_markup={"remove_keyboard": True},  # Убираем клавиатуру с геолокацией
        )
        return

    # --- Шаг 4: предпочтения по темам дайджеста ---
    if state == STATE_ASK_PREFS_TOPICS:
        # Ожидаем числа 1–6, можно через запятую или пробел
        digits = {ch for ch in text if ch in "123456"}
        if not digits:
            logger.warning("Invalid prefs topics input", user_id=user.id, text=text)
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
            "5": "learning",
            "6": "creativity",
        }
        topics = sorted({mapping[d] for d in digits})
        logger.info("Parsed prefs topics", user_id=user.id, topics=topics)

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
            logger.warning("Invalid prefs delivery input", user_id=user.id, text=text)
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.prefs_delivery_invalid"),
                parse_mode="Markdown",
            )
            return

        logger.info(
            "Parsed digest_length_preference",
            user_id=user.id,
            length_code=length_code,
        )

        # Сохраняем в prefs + помечаем онбординг как завершённый
        prefs["digest_length_preference"] = length_code
        prefs[ONBOARDING_STATE_KEY] = STATE_COMPLETE

        # Устанавливаем дефолтное время доставки, если не установлено
        if "delivery_time_local" not in prefs:
            prefs["delivery_time_local"] = "09:00"

        _save_user_prefs(db, user, prefs)

        # Дублируем в отдельные колонки, если они есть на модели
        interests = prefs.get("digest_interests")

        if hasattr(user, "digest_length_preference"):
            try:
                user.digest_length_preference = length_code  # type: ignore[assignment]
            except Exception as e:
                logger.error(
                    "Failed to set digest_length_preference",
                    user_id=user.id,
                    error=str(e),
                )

        if hasattr(user, "digest_interests") and interests is not None:
            try:
                user.digest_interests = interests  # type: ignore[assignment]
            except Exception as e:
                logger.error(
                    "Failed to set digest_interests", user_id=user.id, error=str(e)
                )

        # Устанавливаем дефолтное время доставки
        if hasattr(user, "delivery_time_local"):
            try:
                if not user.delivery_time_local:
                    from datetime import time as time_type

                    user.delivery_time_local = time_type(9, 0)  # type: ignore[assignment]
            except Exception as e:
                logger.error(
                    "Failed to set delivery_time_local", user_id=user.id, error=str(e)
                )

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

                    logger.info(
                        "Display name set", user_id=user.id, name=user.display_name
                    )
            except Exception as e:
                logger.error(
                    "Failed to set display_name", user_id=user.id, error=str(e)
                )

        # Фиксируем все изменения user в БД
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info("Onboarding complete", user_id=user.id)

        send_message(
            chat_id,
            tr(lang, "tg.onboarding.complete"),
            parse_mode="Markdown",
        )
        return

    # На всякий случай: неизвестное состояние → сбрасываем.
    logger.warning("Unknown onboarding state, resetting", user_id=user.id, state=state)
    prefs.pop(ONBOARDING_STATE_KEY, None)
    _save_user_prefs(db, user, prefs)
    send_message(
        chat_id,
        tr(lang, "tg.help.basic"),
        parse_mode="Markdown",
    )


def _handle_settings_text_message(
    db: Session,
    user: models.User,
    chat_id: int,
    text: str,
) -> None:
    """Обработка текстовых сообщений при редактировании настроек через /settings."""
    prefs = _get_user_prefs(user)
    state = prefs.get(SETTINGS_EDIT_STATE_KEY)
    text = (text or "").strip()
    lang = user.locale or "en"

    logger.info(
        "Handling settings edit text message",
        user_id=user.id,
        state=state,
        text_length=len(text),
    )

    if not state:
        # Нет активного состояния редактирования
        return

    # Редактирование даты рождения
    if state == STATE_EDIT_BIRTH_DATE:
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
        prefs.pop(SETTINGS_EDIT_STATE_KEY, None)
        _save_user_prefs(db, user, prefs)

        # Обновляем birth_data таблицу
        birth_time_str = prefs.get("birth_time") or "12:00"
        birth_place = prefs.get("birth_place") or ""

        repo.upsert_birth_data(
            db,
            user_ref=str(user.id),
            birth_date=bdate,
            birth_time=birth_time_str,
            place=birth_place,
            lat=None,
            lon=None,
            tz=None,
        )

        # Пересчитываем geo данные
        ensure_birthdata_geo_for_user(db, user)

        # Инвалидируем natal cache
        db.query(models.NatalCache).filter(
            models.NatalCache.user_id == user.id
        ).delete()
        db.commit()

        logger.info("Birth date updated", user_id=user.id, new_date=str(bdate))
        send_message(
            chat_id,
            tr(lang, "tg.settings.edit.saved"),
            parse_mode="Markdown",
        )
        return

    # Редактирование времени рождения
    if state == STATE_EDIT_BIRTH_TIME:
        lowered = text.lower()
        if lowered in {
            "не знаю",
            "не помню",
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

        time_str = f"{hh:02d}:{mm:02d}"
        prefs["birth_time"] = time_str
        prefs.pop(SETTINGS_EDIT_STATE_KEY, None)
        _save_user_prefs(db, user, prefs)

        # Обновляем birth_data таблицу
        birth_date_str = prefs.get("birth_date")
        if birth_date_str:
            try:
                bdate = datetime.fromisoformat(birth_date_str).date()
            except:
                bdate = None
        else:
            bdate = None

        birth_place = prefs.get("birth_place") or ""

        if bdate:
            repo.upsert_birth_data(
                db,
                user_ref=str(user.id),
                birth_date=bdate,
                birth_time=time_str,
                place=birth_place,
                lat=None,
                lon=None,
                tz=None,
            )

            # Инвалидируем natal cache
            db.query(models.NatalCache).filter(
                models.NatalCache.user_id == user.id
            ).delete()
            db.commit()

        logger.info("Birth time updated", user_id=user.id, new_time=time_str)
        send_message(
            chat_id,
            tr(lang, "tg.settings.edit.saved"),
            parse_mode="Markdown",
        )
        return

    # Редактирование места рождения
    if state == STATE_EDIT_BIRTH_PLACE:
        if not text:
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.birth_place_empty"),
                parse_mode="Markdown",
            )
            return

        prefs["birth_place"] = text
        prefs.pop(SETTINGS_EDIT_STATE_KEY, None)
        _save_user_prefs(db, user, prefs)

        # Обновляем birth_data таблицу
        birth_date_str = prefs.get("birth_date")
        birth_time_str = prefs.get("birth_time") or "12:00"

        if birth_date_str:
            try:
                bdate = datetime.fromisoformat(birth_date_str).date()
            except:
                bdate = None
        else:
            bdate = None

        if bdate:
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

            # Пересчитываем geo данные и timezone
            ensure_birthdata_geo_for_user(db, user)

            # Инвалидируем natal cache
            db.query(models.NatalCache).filter(
                models.NatalCache.user_id == user.id
            ).delete()
            db.commit()

        logger.info("Birth place updated", user_id=user.id, new_place=text)
        send_message(
            chat_id,
            tr(lang, "tg.settings.edit.saved"),
            parse_mode="Markdown",
        )
        return


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
    logger.debug("Incoming Telegram update", update_keys=list(update.keys()))

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
    callback_query_id: Optional[str] = message.get("_callback_query_id")

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

        # ========== 0. LOCATION message (для timezone при онбординге) ==========

        location = message.get("location")
        if location:
            lat = location.get("latitude")
            lon = location.get("longitude")

            # Обрабатываем location только если пользователь в нужном состоянии
            if (
                onboarding_state == STATE_ASK_TIMEZONE_LOCATION
                and lat is not None
                and lon is not None
            ):
                logger.info(
                    "Received location for timezone during onboarding",
                    user_id=user.id,
                    lat=lat,
                    lon=lon,
                )

                # Определяем timezone по координатам
                timezone_str = tz_by_latlon(lat, lon)

                if timezone_str:
                    user.timezone = timezone_str
                    prefs = _get_user_prefs(user)
                    prefs["timezone"] = timezone_str
                    prefs[ONBOARDING_STATE_KEY] = STATE_ASK_PREFS_TOPICS
                    _save_user_prefs(db, user, prefs)

                    logger.info(
                        "Timezone set from location",
                        user_id=user.id,
                        timezone=timezone_str,
                    )

                    # Переходим к следующему шагу и убираем клавиатуру
                    send_message(
                        chat_id,
                        tr(lang, "tg.onboarding.timezone_saved", timezone=timezone_str)
                        + "\n\n"
                        + tr(lang, "tg.onboarding.prefs_topics_prompt"),
                        parse_mode="Markdown",
                        reply_markup={
                            "remove_keyboard": True
                        },  # Убираем клавиатуру с геолокацией
                    )
                    return {"status": "ok"}
                else:
                    # Если не удалось определить timezone, используем fallback
                    logger.warning(
                        "Could not determine timezone from location",
                        user_id=user.id,
                        lat=lat,
                        lon=lon,
                    )
                    prefs = _get_user_prefs(user)
                    prefs[ONBOARDING_STATE_KEY] = STATE_ASK_PREFS_TOPICS
                    _save_user_prefs(db, user, prefs)

                    # Переходим к следующему шагу и убираем клавиатуру
                    send_message(
                        chat_id,
                        tr(lang, "tg.onboarding.prefs_topics_prompt"),
                        parse_mode="Markdown",
                        reply_markup={
                            "remove_keyboard": True
                        },  # Убираем клавиатуру с геолокацией
                    )
                    return {"status": "ok"}
            else:
                # Location получен НЕ в контексте онбординга timezone
                # Это может быть запоздалый клик по кнопке или случайная отправка
                logger.warning(
                    "Received location outside of expected context",
                    user_id=user.id,
                    onboarding_state=onboarding_state,
                    lat=lat,
                    lon=lon,
                )

                # Отправляем понятное сообщение пользователю
                send_message(
                    chat_id,
                    tr(lang, "tg.location.unexpected"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

        # ========== 0. CALLBACK-ветка ==========

        if callback_data:
            # КРИТИЧЕСКИ ВАЖНО: подтверждаем обработку callback_query
            # Без этого Telegram будет повторно отправлять callback_query
            if callback_query_id:
                try:
                    answer_callback_query(callback_query_id)
                except Exception as e:
                    logger.warning(
                        "Failed to answer callback query",
                        callback_query_id=callback_query_id,
                        error=str(e),
                    )

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

            # 2. Settings: доставка (delivery toggle + time)
            if callback_data == "settings_delivery":
                delivery_enabled = getattr(user, "delivery_enabled", True)
                status_key = (
                    "tg.settings.delivery.enabled"
                    if delivery_enabled
                    else "tg.settings.delivery.disabled"
                )
                status_label = tr(lang_code, status_key)

                dt_value = getattr(user, "delivery_time_local", None)
                if dt_value:
                    if hasattr(dt_value, "strftime"):
                        time_label = dt_value.strftime("%H:%M")
                    else:
                        time_label = str(dt_value)
                else:
                    time_label = tr(lang_code, "tg.settings.delivery_time.not_set")

                msg = tr(
                    lang_code,
                    "tg.settings.delivery.submenu",
                    status=status_label,
                    time=time_label,
                )

                toggle_text = tr(
                    lang_code,
                    (
                        "tg.settings.delivery.toggle_off"
                        if delivery_enabled
                        else "tg.settings.delivery.toggle_on"
                    ),
                )

                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": toggle_text,
                                "callback_data": "settings_delivery_toggle",
                            },
                        ],
                        [
                            {
                                "text": tr(
                                    lang_code, "tg.settings.delivery.change_time"
                                ),
                                "callback_data": "settings_delivery_time",
                            },
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

            if callback_data == "settings_delivery_toggle":
                if user.delivery_enabled is None or user.delivery_enabled:
                    user.delivery_enabled = False
                    msg = tr(lang_code, "tg.settings.delivery.toggled_off")
                else:
                    user.delivery_enabled = True
                    dt_value = getattr(user, "delivery_time_local", None)
                    time_str = "09:00"
                    if dt_value:
                        if hasattr(dt_value, "strftime"):
                            time_str = dt_value.strftime("%H:%M")
                        else:
                            time_str = str(dt_value)
                    msg = tr(
                        lang_code, "tg.settings.delivery.toggled_on", time=time_str
                    )

                db.commit()
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            if callback_data == "settings_delivery_time":
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

            # 3. Settings: время доставки (из delivery submenu)
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

            # 4. Settings: interests
            if callback_data == "settings_interests":
                prefs = _get_user_prefs(user)
                current_interests = (
                    prefs.get("digest_interests") or user.digest_interests or []
                )

                interest_options = []
                all_interests = [
                    "work",
                    "relationships",
                    "money",
                    "selfcare",
                    "learning",
                    "creativity",
                ]
                for interest in all_interests:
                    icon = "✅" if interest in current_interests else "☐"
                    label = tr(lang_code, f"tg.settings.interests.{interest}")
                    interest_options.append(f"{icon} {label}")

                options_text = "\n".join(interest_options)
                current_labels = [
                    tr(lang_code, f"tg.settings.interests.{i}")
                    for i in current_interests
                ]
                current_text = ", ".join(current_labels) if current_labels else "—"

                msg = tr(
                    lang_code,
                    "tg.settings.interests.prompt",
                    options=options_text,
                    current=current_text,
                )

                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": tr(lang_code, "tg.settings.interests.work"),
                                "callback_data": "settings_interests_toggle_work",
                            },
                            {
                                "text": tr(
                                    lang_code, "tg.settings.interests.relationships"
                                ),
                                "callback_data": "settings_interests_toggle_relationships",
                            },
                        ],
                        [
                            {
                                "text": tr(lang_code, "tg.settings.interests.money"),
                                "callback_data": "settings_interests_toggle_money",
                            },
                            {
                                "text": tr(lang_code, "tg.settings.interests.selfcare"),
                                "callback_data": "settings_interests_toggle_selfcare",
                            },
                        ],
                        [
                            {
                                "text": tr(lang_code, "tg.settings.interests.learning"),
                                "callback_data": "settings_interests_toggle_learning",
                            },
                            {
                                "text": tr(
                                    lang_code, "tg.settings.interests.creativity"
                                ),
                                "callback_data": "settings_interests_toggle_creativity",
                            },
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

            if callback_data.startswith("settings_interests_toggle_"):
                interest = callback_data.split("settings_interests_toggle_", 1)[1]
                all_interests = [
                    "work",
                    "relationships",
                    "money",
                    "selfcare",
                    "learning",
                    "creativity",
                ]
                if interest not in all_interests:
                    return {"status": "ok"}
                prefs = _get_user_prefs(user)
                interests_list = (
                    prefs.get("digest_interests") or user.digest_interests or []
                )
                interests_list = list(interests_list)  # Ensure it's a list

                if interest in interests_list:
                    interests_list.remove(interest)
                else:
                    interests_list.append(interest)

                prefs["digest_interests"] = interests_list
                user.digest_interests = interests_list
                _save_user_prefs(db, user, prefs)
                # Инвалидация кэша дайджеста: при смене интересов следующий /today пересчитается
                removed = TODAY_CACHE.delete_by_prefix(f"tg:today:{user.id}:")
                if removed:
                    logger.info(
                        "Invalidated today cache for user after interests change",
                        user_id=user.id,
                        keys_removed=removed,
                    )

                interest_labels = [
                    tr(lang_code, f"tg.settings.interests.{i}") for i in interests_list
                ]
                interests_str = ", ".join(interest_labels) if interest_labels else "—"

                msg = tr(
                    lang_code, "tg.settings.interests.updated", interests=interests_str
                )
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 5. Settings: digest length
            if callback_data == "settings_length":
                msg = tr(lang_code, "tg.settings.length.prompt")
                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": tr(lang_code, "tg.settings.length.short"),
                                "callback_data": "settings_length_short",
                            },
                        ],
                        [
                            {
                                "text": tr(lang_code, "tg.settings.length.medium"),
                                "callback_data": "settings_length_medium",
                            },
                        ],
                        [
                            {
                                "text": tr(lang_code, "tg.settings.length.long"),
                                "callback_data": "settings_length_long",
                            },
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

            if callback_data.startswith("settings_length_"):
                length = callback_data.split("settings_length_", 1)[1]
                if length not in ("short", "medium", "long"):
                    length = "medium"

                prefs = _get_user_prefs(user)
                prefs["digest_length_preference"] = length
                user.digest_length_preference = length
                _save_user_prefs(db, user, prefs)

                length_label = tr(lang_code, f"tg.settings.length.{length}")
                msg = tr(lang_code, "tg.settings.length.updated", length=length_label)
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 6. Settings: birth data edit (set state for text input)
            if callback_data == "settings_birth_date":
                prefs = _get_user_prefs(user)
                prefs[SETTINGS_EDIT_STATE_KEY] = STATE_EDIT_BIRTH_DATE
                _save_user_prefs(db, user, prefs)

                msg = tr(lang_code, "tg.settings.edit.birth_date_prompt")
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            if callback_data == "settings_birth_time":
                prefs = _get_user_prefs(user)
                prefs[SETTINGS_EDIT_STATE_KEY] = STATE_EDIT_BIRTH_TIME
                _save_user_prefs(db, user, prefs)

                msg = tr(lang_code, "tg.settings.edit.birth_time_prompt")
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            if callback_data == "settings_birth_place":
                prefs = _get_user_prefs(user)
                prefs[SETTINGS_EDIT_STATE_KEY] = STATE_EDIT_BIRTH_PLACE
                _save_user_prefs(db, user, prefs)

                msg = tr(lang_code, "tg.settings.edit.birth_place_prompt")
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            # 7. Settings: upgrade
            if callback_data == "settings_upgrade":
                plan_code = get_user_plan(db, user.id)

                if plan_code in ("full", "internal"):
                    i18n_key = "tg.upgrade.already_full"
                else:
                    i18n_key = "tg.upgrade.summary"

                plan_name = tr(lang_code, plan_title_key(plan_code))
                msg = tr(lang_code, i18n_key, plan_name=plan_name)

                send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            # 8. Feedback по дайджесту
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

        # ========== 2. /continue (продолжить прерванный онбординг) ==========

        if text.startswith("/continue"):
            current_state = _get_onboarding_state(user)

            if not current_state or current_state == STATE_COMPLETE:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.continue.already_complete"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            # Продолжаем с того места, где остановились
            if current_state == STATE_AGE_GATE:
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
                send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_BIRTH_DATE:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.start.ask_birth_date"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_BIRTH_TIME:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.birth_time_prompt"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_BIRTH_PLACE:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.birth_place_prompt"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_TIMEZONE_LOCATION:
                # Это тот случай, который прервал пользователь
                msg = tr(lang, "tg.onboarding.timezone_location_prompt")

                # Кнопка для отправки локации
                keyboard = {
                    "keyboard": [
                        [
                            {
                                "text": tr(lang, "tg.onboarding.timezone_location_btn"),
                                "request_location": True,
                            }
                        ],
                        [
                            {
                                "text": tr(
                                    lang, "tg.onboarding.timezone_location_skip"
                                ),
                            }
                        ],
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                }

                send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_PREFS_TOPICS:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.prefs_topics_prompt"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            elif current_state == STATE_ASK_PREFS_DELIVERY:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.prefs_delivery_prompt"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            # Если состояние неизвестно, говорим использовать /start
            send_message(
                chat_id=chat_id,
                text=tr(lang, "tg.continue.unknown_state"),
                parse_mode="Markdown",
            )
            return {"status": "ok"}

        # ========= 4. /today =========

        if text.startswith("/today"):
            # Проверка завершённости онбординга
            onboarding_state = _get_onboarding_state(user)
            if onboarding_state and onboarding_state != STATE_COMPLETE:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.incomplete"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            # Проверка наличия timezone
            if not user.timezone:
                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.onboarding.incomplete"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

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

            # 4) КРИТИЧНО: применяем plan cap (минимум из user_pref и plan_cap)
            # Порядок ограничений: short < medium < long
            length_order = {"short": 0, "medium": 1, "long": 2}
            user_order = length_order.get(length_pref, 0)
            cap_order = length_order.get(digest_cap, 0)

            # Берём минимальную (более ограничивающую) длину
            if user_order > cap_order:
                length_pref = digest_cap
                logger.info(
                    "User digest length clamped by plan cap",
                    user_id=user.id,
                    user_preference=user.digest_length_preference
                    or prefs.get("digest_length_preference"),
                    plan_cap=digest_cap,
                    final_length=length_pref,
                )

            # Конфиг для модуля дайджеста
            digest_config: dict[str, object] = {
                "time_local": tg_prefs.time_local,
                "length": length_pref,
            }

            # Интересы для ключа кэша: при смене интересов дайджест пересчитывается
            prefs_today = _get_user_prefs(user)
            interests_raw = (
                prefs_today.get("digest_interests")
                or getattr(user, "digest_interests", None)
                or ["general"]
            )
            interests_for_key = sorted(
                x
                for x in (
                    [
                        str(i).strip()
                        for i in (
                            interests_raw
                            if isinstance(interests_raw, list)
                            else [interests_raw]
                        )
                    ]
                )
                if x
            ) or ["general"]
            cache_key = _cache_key_today(
                user.id, today, lang, length_pref, interests_for_key
            )
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
                logger.error(
                    "/today failed", user_id=user.id, error=str(exc), exc_info=True
                )
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
            logger.info("Handling /upgrade", user_id=user.id)

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

            # Birth data из prefs
            prefs = _get_user_prefs(user)
            birth_date = prefs.get("birth_date", "—")
            if birth_date and birth_date != "—":
                try:
                    # Форматируем дату из ISO в DD.MM.YYYY
                    bd = datetime.fromisoformat(birth_date).date()
                    birth_date = bd.strftime("%d.%m.%Y")
                except:
                    pass

            birth_time = prefs.get("birth_time", "—")
            birth_place = prefs.get("birth_place", "—")

            # Интересы
            interests_list = (
                prefs.get("digest_interests") or user.digest_interests or []
            )
            if interests_list:
                interests_labels = []
                interest_map = {
                    "work": tr(lang_code, "tg.settings.interests.work"),
                    "relationships": tr(
                        lang_code, "tg.settings.interests.relationships"
                    ),
                    "money": tr(lang_code, "tg.settings.interests.money"),
                    "selfcare": tr(lang_code, "tg.settings.interests.selfcare"),
                    "learning": tr(lang_code, "tg.settings.interests.learning"),
                    "creativity": tr(lang_code, "tg.settings.interests.creativity"),
                }
                for interest in interests_list:
                    interests_labels.append(interest_map.get(interest, interest))
                interests_str = ", ".join(interests_labels)
            else:
                interests_str = "—"

            # Длина дайджеста
            length_pref = (
                prefs.get("digest_length_preference")
                or user.digest_length_preference
                or "medium"
            )
            length_labels = {
                "short": tr(lang_code, "tg.settings.length.short"),
                "medium": tr(lang_code, "tg.settings.length.medium"),
                "long": tr(lang_code, "tg.settings.length.long"),
            }
            length_str = length_labels.get(length_pref, length_pref)

            msg = tr(
                lang_code,
                "tg.settings.summary",
                language=lang_label,
                plan_name=plan_name,
                delivery_status=delivery_status,
                delivery_time=delivery_time_label,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                interests=interests_str,
                length=length_str,
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.language"),
                            "callback_data": "settings_lang",
                        },
                        {
                            "text": tr(lang_code, "tg.settings.btn.delivery"),
                            "callback_data": "settings_delivery",
                        },
                    ],
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.interests"),
                            "callback_data": "settings_interests",
                        },
                        {
                            "text": tr(lang_code, "tg.settings.btn.length"),
                            "callback_data": "settings_length",
                        },
                    ],
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.birth_date"),
                            "callback_data": "settings_birth_date",
                        },
                        {
                            "text": tr(lang_code, "tg.settings.btn.birth_time"),
                            "callback_data": "settings_birth_time",
                        },
                    ],
                    [
                        {
                            "text": tr(lang_code, "tg.settings.btn.birth_place"),
                            "callback_data": "settings_birth_place",
                        },
                        {
                            "text": tr(lang_code, "tg.settings.btn.upgrade"),
                            "callback_data": "settings_upgrade",
                        },
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

        # ========== 8.5. Редактирование настроек ==========

        prefs = _get_user_prefs(user)
        settings_edit_state = prefs.get(SETTINGS_EDIT_STATE_KEY)
        if settings_edit_state and not text.startswith("/"):
            _handle_settings_text_message(db, user, chat_id, text)
            return {"status": "ok"}

        # ========== 9. Help по умолчанию ==========

        send_message(chat_id=chat_id, text=tr(lang, "tg.help.basic"))
        return {"status": "ok"}
