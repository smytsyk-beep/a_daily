# src/app/routes_telegram.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, repo
from app.modules import daily_digest as daily_digest_module
from app.telegram_client import send_message
from app.telegram_prefs import get_telegram_prefs_from_user
from app.repo import session_scope

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


# ---------- Вспомогательные функции ----------


def _safe_prefs_dict(user: models.User) -> Dict[str, Any]:
    """
    Аккуратно достаём user.prefs как dict.
    Если там None или что-то странное — возвращаем пустой словарь.
    """
    raw = getattr(user, "prefs", None)
    if not isinstance(raw, dict):
        return {}
    return dict(raw)


def _get_onboarding_state(user: models.User) -> Optional[str]:
    prefs = _safe_prefs_dict(user)
    return prefs.get(ONBOARDING_STATE_KEY)


def _set_onboarding_state(user: models.User, state: Optional[str]) -> Dict[str, Any]:
    """
    Обновляет состояние онбординга в user.prefs и возвращает актуальный dict.
    Коммит делается снаружи.
    """
    prefs = _safe_prefs_dict(user)

    if state is None:
        prefs.pop(ONBOARDING_STATE_KEY, None)
    else:
        prefs[ONBOARDING_STATE_KEY] = state

    user.prefs = prefs
    return prefs


def _get_user_prefs(user: models.User) -> Dict[str, Any]:
    """Унифицированный доступ к prefs как к dict."""
    return _safe_prefs_dict(user)


def _save_user_prefs(db: Session, user: models.User, prefs: Dict[str, Any]) -> None:
    """Сохраняем prefs в БД с коммитом."""
    user.prefs = prefs
    db.add(user)
    db.commit()
    db.refresh(user)


def _get_or_create_user_by_tg_id(
    db: Session,
    tg_user_id: int,
    username: Optional[str],
) -> models.User:
    """
    Находит пользователя по tg_user_id, если нет — создаёт нового.
    """
    tg_str = str(tg_user_id)

    user = db.query(models.User).filter(models.User.tg_user_id == tg_str).first()
    if user:
        print(f"[TG] Existing user loaded by tg_user_id={tg_str}, id={user.id}")
        return user

    user = models.User(
        tg_user_id=tg_str,
        locale="en",  # дефолт, позже можно брать из Telegram language_code
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[TG] New user created: id={user.id}, tg_user_id={tg_str}")
    return user


def _extract_message(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Возвращает "обычное" сообщение, если это message,
    или pseudo-message, сформированное из callback_query.

    Для callback_query:
      - chat берём из message
      - from ПЕРЕЗАПИСЫВАЕМ на callback_query["from"]
      - data кладём в "_callback_data"
    """
    if "message" in update:
        return update["message"]

    if "callback_query" in update:
        cq = update["callback_query"]
        msg = cq.get("message") or {}
        # ВАЖНО: именно user, который нажал кнопку
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
    """
    Обрабатываем свободный текст во время онбординга.
    """
    prefs = _get_user_prefs(user)
    state = prefs.get(ONBOARDING_STATE_KEY)
    text = (text or "").strip()

    print(
        f"[TG] _handle_onboarding_text_message: user_id={user.id}, "
        f"state={state!r}, text={text!r}, prefs={prefs}"
    )

    # Если состояние не выставлено или уже complete — даём help и выходим.
    if not state or state == STATE_COMPLETE:
        print("[TG] Onboarding state empty/complete inside handler → help only")
        send_message(
            chat_id,
            "I understand /start, /today and /snooze for now 🙂",
        )
        return

    # --- Шаг 1: дата рождения ---
    if state == STATE_ASK_BIRTH_DATE:
        try:
            bdate = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            print("[TG] Birth date parse failed")
            send_message(
                chat_id,
                "Please send your birth date in format *DD.MM.YYYY*, for example *12.10.1980*.",
                parse_mode="Markdown",
            )
            return

        prefs["birth_date"] = bdate.isoformat()
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_BIRTH_TIME
        _save_user_prefs(db, user, prefs)
        print(
            f"[TG] Birth date saved: {bdate.isoformat()} → state={STATE_ASK_BIRTH_TIME}"
        )

        send_message(
            chat_id,
            "Got it ✅\n\nNow send your birth time in format *HH:MM* (24h), or type *Не знаю* if you’re not sure.",
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
        }:
            hh, mm = 12, 0
            print("[TG] Birth time unknown → using 12:00")
        else:
            try:
                t = datetime.strptime(text, "%H:%M").time()
            except ValueError:
                print("[TG] Birth time parse failed")
                send_message(
                    chat_id,
                    "Please send your birth time in format *HH:MM* (for example *07:30*), or type *Не знаю*.",
                    parse_mode="Markdown",
                )
                return
            hh, mm = t.hour, t.minute
            print(f"[TG] Birth time parsed: {hh:02d}:{mm:02d}")

        prefs["birth_time"] = f"{hh:02d}:{mm:02d}"
        prefs[ONBOARDING_STATE_KEY] = STATE_ASK_BIRTH_PLACE
        _save_user_prefs(db, user, prefs)
        print(f"[TG] Birth time saved → state={STATE_ASK_BIRTH_PLACE}")

        send_message(
            chat_id,
            "Thanks! 🙌\nNow type your *place of birth* — city and country, for example: *“Kyiv, Ukraine”*.",
            parse_mode="Markdown",
        )
        return

    # --- Шаг 3: место рождения + запись BirthData ---
    if state == STATE_ASK_BIRTH_PLACE:
        if not text:
            print("[TG] Empty birth place")
            send_message(
                chat_id,
                "Please enter your place of birth, e.g. *“Kyiv, Ukraine”*.",
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
            # ВАЖНО: используем внутренний PK пользователя, а не tg_user_id,
            # чтобы не ловить integer out of range.
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

        prefs[ONBOARDING_STATE_KEY] = STATE_COMPLETE
        _save_user_prefs(db, user, prefs)
        print(f"[TG] Onboarding complete for user_id={user.id}")

        send_message(
            chat_id,
            (
                "Great, your birth data is saved ✅\n\n"
                "Now you can use /today to get your daily digest, "
                "or /snooze to pause notifications."
            ),
        )
        return

    # На всякий случай: неизвестное состояние → сбрасываем.
    print(f"[TG] Unknown onboarding state inside handler: {state!r}, resetting")
    prefs.pop(ONBOARDING_STATE_KEY, None)
    _save_user_prefs(db, user, prefs)
    send_message(
        chat_id,
        "I understand /start, /today and /snooze for now 🙂",
    )


# ---------- Основной webhook ----------


@router.post("/webhook", status_code=200)
async def telegram_webhook(
    request: Request,
) -> Dict[str, str]:
    """
    Webhook-эндпоинт для Telegram.
    """
    update = await request.json()
    print(f"[TG] Incoming update: {update}")

    message = _extract_message(update)
    if not message:
        print("[TG] No message/callback in update → ignored")
        return {"status": "ignored"}

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chat_id missing",
        )

    text: str = (message.get("text") or "").strip()
    callback_data: Optional[str] = message.get("_callback_data")

    from_user = message.get("from") or {}
    tg_user_id = from_user.get("id")
    username = from_user.get("username")

    if tg_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from.id missing",
        )

    print(
        f"[TG] Parsed message: chat_id={chat_id}, tg_user_id={tg_user_id}, "
        f"text={text!r}, callback_data={callback_data!r}"
    )

    with session_scope() as db:
        user = _get_or_create_user_by_tg_id(
            db,
            tg_user_id=tg_user_id,
            username=username,
        )

        onboarding_state = _get_onboarding_state(user)
        tg_prefs = get_telegram_prefs_from_user(user)

        print(
            f"[TG] Current user: id={user.id}, tg_user_id={user.tg_user_id}, "
            f"onboarding_state={onboarding_state!r}, prefs={_safe_prefs_dict(user)}"
        )

        # ========== 0. CALLBACK-ветка ==========

        if callback_data:
            print(f"[TG] Handling callback_data={callback_data!r}")
            # 0.1 Age-gate callbacks
            if callback_data == "age_yes":
                now = datetime.utcnow()
                user.age_gate_accepted_at = now
                user.disclaimer_accepted_at = now
                user.birthdata_consent_at = now

                _set_onboarding_state(user, STATE_ASK_BIRTH_DATE)
                db.commit()

                print(
                    f"[TG] Age gate accepted for user_id={user.id}, "
                    f"state → {STATE_ASK_BIRTH_DATE}"
                )

                msg = (
                    "Thank you! ✅\n\n"
                    "Let’s set up your profile.\n"
                    "Please send your birth date in format *DD.MM.YYYY*."
                )
                send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                return {"status": "ok"}

            if callback_data == "age_no":
                _set_onboarding_state(user, None)
                db.commit()

                print(f"[TG] Age gate declined for user_id={user.id}")

                msg = (
                    "Understood. AstroDaily is available only for users 18+.\n"
                    "If this was a mistake, you can send /start again later."
                )
                send_message(chat_id=chat_id, text=msg)
                return {"status": "ok"}

            # 0.2 Фидбек по дайджесту
            if callback_data == "dd_like":
                ack = "Got it 👍 Thanks for your feedback!"
            elif callback_data == "dd_dislike":
                ack = "Got it 👎 I’ll try to adjust future digests."
            elif callback_data == "dd_hide":
                ack = "Okay 🙈 I’ll try to show less of this topic."
            else:
                ack = "Thanks for your feedback!"

            print(f"[TG] Feedback callback handled: {callback_data!r}")
            send_message(chat_id=chat_id, text=ack)
            return {"status": "ok"}

        # ========== 1. /start ==========

        if text.startswith("/start"):
            print("[TG] Handling /start")
            # Новый пользователь без age-gate → сначала спрашиваем 18+
            if not user.age_gate_accepted_at:
                if user.delivery_enabled is not True:
                    user.delivery_enabled = True

                _set_onboarding_state(user, STATE_AGE_GATE)

                msg = (
                    "Hi! I’m *AstroDaily* bot 🌌\n\n"
                    "Before we start, I need to confirm that you are *18+* and that you understand "
                    "this is *not a medical, financial or legal service* and is provided "
                    "*for entertainment purposes only*.\n\n"
                    "Do you confirm that you are 18+ and agree with this?"
                )
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "✅ Yes, I’m 18+",
                                "callback_data": "age_yes",
                            },
                            {
                                "text": "❌ No",
                                "callback_data": "age_no",
                            },
                        ]
                    ]
                }

                db.commit()
                print(
                    f"[TG] Age gate question sent, state={_get_onboarding_state(user)!r}"
                )
                send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                return {"status": "ok"}

            # age-gate уже принят → если нет birth-data, продолжим онбординг
            prefs = _safe_prefs_dict(user)
            has_birth_data = all(
                key in prefs for key in ("birth_date", "birth_time", "birth_place")
            )
            print(
                f"[TG] /start with age_gate accepted, has_birth_data={has_birth_data}, prefs={prefs}"
            )

            if not has_birth_data:
                _set_onboarding_state(user, STATE_ASK_BIRTH_DATE)
                db.commit()
                print(
                    f"[TG] /start re-enters onboarding, state={_get_onboarding_state(user)!r}"
                )
                send_message(
                    chat_id=chat_id,
                    text=(
                        "Let’s set up your profile.\n"
                        "Please send your birth date in format *DD.MM.YYYY*."
                    ),
                    parse_mode="Markdown",
                )
                return {"status": "ok"}

            # birth data уже есть → обычный welcome
            _set_onboarding_state(user, STATE_COMPLETE)

            if user.delivery_enabled is not True:
                user.delivery_enabled = True

            db.commit()

            print(f"[TG] /start for fully onboarded user_id={user.id}")

            welcome = (
                "Hi! I’m your *AstroDaily* bot.\n\n"
                "I’ll send you a short daily astro-digest based on your birth data "
                "and current sky events.\n\n"
                "Use /today to get your digest for today.\n"
                "Use /snooze to pause/resume daily delivery."
            )
            send_message(chat_id=chat_id, text=welcome, parse_mode="Markdown")
            return {"status": "ok"}

        # ========== 2. /today ==========

        if text.startswith("/today"):
            print(f"[TG] Handling /today for user_id={user.id}")
            today = date.today()  # пока не используем, но может пригодиться

            atoms = daily_digest_module.compute(
                user_id=user.id,
                config={"time_local": tg_prefs.time_local},
            )

            if not atoms:
                print("[TG] daily_digest_module.compute returned empty list")
                send_message(
                    chat_id=chat_id,
                    text="I couldn’t build your digest for today. Please try again later.",
                )
                return {"status": "ok"}

            atom = atoms[0]
            title = atom.get("title") or "Your daily digest"
            body = atom.get("body") or ""
            affirmation = atom.get("affirmation")

            lines = [f"✨ *{title}* ✨", "", body]
            if affirmation:
                lines.extend(["", f"_Affirmation:_ {affirmation}"])

            full_text = "\n".join(lines)

            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "👍 Like", "callback_data": "dd_like"},
                        {"text": "👎 Not for me", "callback_data": "dd_dislike"},
                        {"text": "🙈 Hide topic", "callback_data": "dd_hide"},
                    ]
                ]
            }

            send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
            print("[TG] /today digest sent")
            return {"status": "ok"}

        # ========== 3. /snooze ==========

        if text.startswith("/snooze"):
            print(f"[TG] Handling /snooze for user_id={user.id}")
            if user.delivery_enabled is None or user.delivery_enabled:
                user.delivery_enabled = False
                msg = (
                    "⏸ Daily delivery *paused*.\n"
                    "Send /snooze again to resume your digests."
                )
            else:
                user.delivery_enabled = True
                msg = (
                    "▶️ Daily delivery *resumed*.\n"
                    "You’ll start receiving digests again."
                )

            db.commit()
            send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            print(f"[TG] /snooze toggled, delivery_enabled={user.delivery_enabled}")
            return {"status": "ok"}

        # ========== 4. Незавершённый онбординг ==========

        if (
            onboarding_state
            and onboarding_state != STATE_COMPLETE
            and not text.startswith("/")
        ):
            print(
                f"[TG] Routing free text into onboarding handler, "
                f"state={onboarding_state!r}, text={text!r}"
            )
            _handle_onboarding_text_message(db, user, chat_id, text)
            return {"status": "ok"}

        # ========== 5. Help по умолчанию ==========

        print(
            f"[TG] Default help branch, onboarding_state={onboarding_state!r}, text={text!r}"
        )
        send_message(
            chat_id=chat_id,
            text="I understand /start, /today and /snooze for now 🙂",
        )
        return {"status": "ok"}
