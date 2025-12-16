# src/app/telegram_worker.py
from __future__ import annotations

from datetime import date
from typing import Optional

from app import models
from app.repo import session_scope
from app.telegram_prefs import get_telegram_prefs_from_user
from app.modules import daily_digest as daily_digest_module
from app.telegram_client import send_message


def _build_reply_markup() -> dict:
    """
    Inline-кнопки фидбека для дневного дайджеста.
    Используем те же callback_data, что и в routes_telegram.
    """
    return {
        "inline_keyboard": [
            [
                {"text": "👍 Like", "callback_data": "dd_like"},
                {"text": "👎 Not for me", "callback_data": "dd_dislike"},
                {"text": "🙈 Hide topic", "callback_data": "dd_hide"},
            ]
        ]
    }


def _send_digest_for_user(user: models.User, on_date: date) -> bool:
    """
    Строит дайджест для одного пользователя и отправляет его в Telegram.

    Возвращает True, если сообщение было отправлено, иначе False.
    """
    if not user.tg_user_id:
        return False

    prefs = get_telegram_prefs_from_user(user)

    atoms = daily_digest_module.compute(
        user_id=user.tg_user_id,
        config={"time_local": prefs.time_local},
    )
    if not atoms:
        return False

    atom = atoms[0]
    title = atom.get("title") or "Your daily digest"
    body = atom.get("body") or ""
    affirmation = atom.get("affirmation")

    lines = [f"✨ *{title}* ✨", "", body]
    if affirmation:
        lines.extend(["", f"_Affirmation:_ {affirmation}"])

    full_text = "\n".join(lines)

    reply_markup = _build_reply_markup()

    # chat_id = tg_user_id (для приватных чатов)
    chat_id = int(user.tg_user_id)

    send_message(
        chat_id=chat_id,
        text=full_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return True


def send_daily_digests_for_day(on_date: Optional[date] = None) -> int:
    """
    Worker-функция под cron/задачу:

    - находит всех пользователей с включённой доставкой (delivery_enabled = True)
      и заданным tg_user_id;
    - для каждого строит дневной дайджест и отправляет его в Telegram;
    - возвращает количество успешно отправленных сообщений.

    В проде можно вызывать её из отдельного процесса/скрипта, например:

        from datetime import date
        from app.telegram_worker import send_daily_digests_for_day

        if __name__ == "__main__":
            send_daily_digests_for_day(date.today())
    """
    if on_date is None:
        on_date = date.today()

    sent_count = 0

    with session_scope() as db:
        users = (
            db.query(models.User)
            .filter(models.User.tg_user_id.isnot(None))
            .filter(models.User.delivery_enabled.is_(True))
            .all()
        )

        for user in users:
            if _send_digest_for_user(user, on_date):
                sent_count += 1

    return sent_count
