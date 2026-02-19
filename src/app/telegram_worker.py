# src/app/telegram_worker.py
from __future__ import annotations

from datetime import date
from typing import Optional

from app import models
from app.repo import session_scope
from app.telegram_prefs import get_telegram_prefs_from_user
from app.modules import daily_digest as daily_digest_module
from app.telegram_client import send_message
from common.plans import get_user_plan
from common.plans import get_plan_runtime_config


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


def _send_digest_for_user(
    user: models.User,
    on_date: date,
    length_override: Optional[str] = None,
) -> bool:
    """
    Построить и отправить дайджест одному пользователю.
    Возвращает True, если сообщение реально отправлено.
    """
    if not user.tg_user_id:
        # Пользователь ещё не связал Telegram — ничего не отправляем
        return False

    prefs = get_telegram_prefs_from_user(user)

    # Конфиг для модуля дайджеста
    digest_config: dict[str, object] = {"time_local": prefs.time_local}
    if length_override:
        # План может ограничивать максимальную длину текста
        digest_config["length"] = length_override

    # ВАЖНО: в compute всегда передаём internal user.id, не tg_user_id
    atoms = daily_digest_module.compute(
        user_id=user.id,
        config=digest_config,
    )
    if not atoms:
        # Нечего отправлять (например, полностью тихий день)
        return False

    # Для MVP берём первый (главный) блок дайджеста
    atom = atoms[0]
    title = atom.get("title") or atom.get("topic_tag") or "Your day"
    body = atom.get("copy_long") or atom.get("body") or ""
    affirmation = atom.get("cta") or atom.get("affirmation")

    header_lines: list[str] = [
        f"✨ {title} ✨",
        "",
        body.strip(),
    ]
    if affirmation:
        header_lines.extend(
            [
                "",
                "Аффирмация дня:",
                affirmation.strip(),
            ]
        )

    full_text = "\n".join(header_lines)

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
            # Определяем актуальный план пользователя и ограничения по длине дайджеста
            try:
                # ВАЖНО: здесь раньше был today, которого не существовало —
                # используем on_date как опорную дату.
                user_plan = get_user_plan(db, user.id, today=on_date)
                plan_cfg = get_plan_runtime_config(user_plan.code)
                digest_cap = plan_cfg.digest_cap

                # Читаем пользовательскую настройку длины
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

                # 4) Применяем plan cap (минимум из user_pref и plan_cap)
                length_order = {"short": 0, "medium": 1, "long": 2}
                user_order = length_order.get(length_pref, 0)
                cap_order = length_order.get(digest_cap, 0)

                if user_order > cap_order:
                    length_pref = digest_cap
                    print(
                        f"[TG] User {user.id} digest length clamped by plan: "
                        f"preference={length_pref} → cap={digest_cap}"
                    )

                length_override = length_pref

            except Exception as exc:
                # Не даём проблемам с планами ломать воркер:
                # в случае ошибки используем длину по умолчанию
                print(f"[TG] get_user_plan failed for user_id={user.id}: {exc!r}")
                length_override = None

            if _send_digest_for_user(user, on_date, length_override=length_override):
                sent_count += 1

    return sent_count
