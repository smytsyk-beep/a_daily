# tests/test_telegram_worker.py

from __future__ import annotations

from contextlib import contextmanager
from datetime import date

from app.db import SessionLocal
from app import models
from app.telegram_worker import send_daily_digests_for_day


def test_send_daily_digests_for_day_sends_only_to_enabled_users(monkeypatch):
    sent_calls: list[dict] = []

    # ---- подмена send_message, чтобы не ходить в Telegram ----
    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent_calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )

    monkeypatch.setattr("app.telegram_worker.send_message", fake_send_message)

    # сюда положим внутренний user.id, чтобы использовать его и в fake_compute, и в ассертах
    user1_id: int | None = None

    # ---- подмена daily_digest.compute, чтобы не зависеть от RAG/LLM ----
    def fake_compute(user_id: int, config=None):
        # убеждаемся, что воркер передал во внутрь именно internal id
        assert user1_id is None or user_id == user1_id

        return [
            {
                "title": f"Digest for {user_id}",
                "body": "Test body",
                "affirmation": "Test affirmation",
                "topic_tag": "generic_day_overview",
                "weight": 1.0,
            }
        ]

    monkeypatch.setattr(
        "app.telegram_worker.daily_digest_module.compute",
        fake_compute,
    )

    # ---- подмена session_scope внутри telegram_worker ----
    @contextmanager
    def fake_session_scope():
        nonlocal user1_id

        db = SessionLocal()
        try:
            # 1) Выключаем доставку для всех существующих пользователей с tg_user_id
            db.query(models.User).filter(models.User.tg_user_id.isnot(None)).update(
                {models.User.delivery_enabled: False},
                synchronize_session=False,
            )
            db.commit()

            # 2) user1: включена доставка, есть tg_user_id -> должен получить сообщение
            user1 = (
                db.query(models.User).filter(models.User.tg_user_id == "1001").first()
            )
            if user1 is None:
                user1 = models.User(
                    tg_user_id="1001",
                    locale="en",
                    delivery_enabled=True,
                )
                db.add(user1)
            else:
                user1.delivery_enabled = True

            # 3) user2: отключена доставка -> не должен получать
            user2 = (
                db.query(models.User).filter(models.User.tg_user_id == "1002").first()
            )
            if user2 is None:
                user2 = models.User(
                    tg_user_id="1002",
                    locale="en",
                    delivery_enabled=False,
                )
                db.add(user2)
            else:
                user2.delivery_enabled = False

            db.commit()

            # сохраняем внутренний id user1 для проверок ниже
            user1_id = user1.id

            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.telegram_worker.session_scope", fake_session_scope)

    # ---- выполняем worker ----
    count = send_daily_digests_for_day(on_date=date(2025, 1, 1))

    # 1 сообщение (только user1)
    assert count == 1
    assert len(sent_calls) == 1

    assert user1_id is not None

    call = sent_calls[0]
    # chat_id = tg_user_id (строка "1001" превращается в int 1001 в воркере)
    assert call["chat_id"] == 1001

    # внутри текста теперь должен быть internal user.id
    assert f"Digest for {user1_id}" in call["text"]
    assert "Test body" in call["text"]
    assert "Test affirmation" in call["text"]
    assert call["parse_mode"] == "Markdown"

    # Проверяем, что есть inline-кнопки фидбека
    rm = call["reply_markup"]
    assert isinstance(rm, dict)
    assert "inline_keyboard" in rm
    buttons = rm["inline_keyboard"][0]
    callback_data_values = {btn["callback_data"] for btn in buttons}
    assert {"dd_like", "dd_dislike", "dd_hide"} <= callback_data_values
