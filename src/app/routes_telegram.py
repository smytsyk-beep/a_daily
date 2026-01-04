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
) -> models.User:
    tg_str = str(tg_user_id)
    normalized = normalize_locale(language_code)

    user = db.query(models.User).filter(models.User.tg_user_id == tg_str).first()
    if user:
        prefs = _safe_prefs_dict(user)
        if not prefs.get("locale_manual"):
            if user.locale in (None, "", "en") and normalized != user.locale:
                user.locale = normalized
                db.commit()
                db.refresh(user)
        return user

    user = models.User(
        tg_user_id=tg_str,
        locale=normalized,
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
            chat_id, tr(lang, "tg.onboarding.birth_time_prompt"), parse_mode="Markdown"
        )
        return

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
            chat_id, tr(lang, "tg.onboarding.birth_place_prompt"), parse_mode="Markdown"
        )
        return

    if state == STATE_ASK_BIRTH_PLACE:
        if not text:
            send_message(
                chat_id,
                tr(lang, "tg.onboarding.birth_place_empty"),
                parse_mode="Markdown",
            )
            return

        prefs["birth_place"] = text
        _save_user_prefs(db, user, prefs)

        birth_date_str = prefs.get("birth_date")
        birth_time_str = prefs.get("birth_time") or "12:00"

        try:
            bdate = (
                datetime.fromisoformat(birth_date_str).date()
                if birth_date_str
                else None
            )
        except Exception:

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
            ensure_birthdata_geo_for_user(db, user)

        prefs[ONBOARDING_STATE_KEY] = STATE_COMPLETE
        _save_user_prefs(db, user, prefs)

        send_message(chat_id, tr(lang, "tg.onboarding.complete"))
        return

    prefs.pop(ONBOARDING_STATE_KEY, None)
    _save_user_prefs(db, user, prefs)
    send_message(chat_id, tr(lang, "tg.help.basic"))


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
        )

        onboarding_state = _get_onboarding_state(user)
        tg_prefs = get_telegram_prefs_from_user(user)
        lang = user.locale

        # ========== 0. CALLBACK-ветка ==========

        if callback_data:

            if callback_data == "age_yes":
                now = datetime.utcnow()
                user.age_gate_accepted_at = now
                user.disclaimer_accepted_at = now
                user.birthdata_consent_at = now

                _set_onboarding_state(user, STATE_ASK_BIRTH_DATE)
                db.commit()

                send_message(
                    chat_id=chat_id,
                    text=tr(lang, "tg.age_gate.accepted"),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            if callback_data == "age_no":
                _set_onboarding_state(user, None)
                db.commit()

                send_message(chat_id=chat_id, text=tr(lang, "tg.age_gate.declined"))
                return {"status": "ok"}

            if callback_data == "dd_like":
                ack = tr(lang, "tg.feedback.like_ack")
            elif callback_data == "dd_dislike":
                ack = tr(lang, "tg.feedback.dislike_ack")
            elif callback_data == "dd_hide":
                ack = tr(lang, "tg.feedback.hide_ack")
            else:
                ack = tr(lang, "tg.feedback.generic_ack")

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

        # ========== 2. /today ==========

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

            plan_code, plan_cfg = _get_user_plan_for_db(db, user)
            digest_cap = plan_cfg.digest_cap

            cache_key = _cache_key_today(user.id, today, lang, digest_cap)
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

            digest_config: dict[str, object] = {
                "time_local": tg_prefs.time_local,
                "length": digest_cap,
            }

            try:
                atoms = daily_digest_module.compute(
                    user_id=user.id, config=digest_config
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

        # ========== 6. Незавершённый онбординг ==========

        if (
            onboarding_state
            and onboarding_state != STATE_COMPLETE
            and not text.startswith("/")
        ):
            _handle_onboarding_text_message(db, user, chat_id, text)
            return {"status": "ok"}

        # ========== 7. Help по умолчанию ==========

        send_message(chat_id=chat_id, text=tr(lang, "tg.help.basic"))
        return {"status": "ok"}
