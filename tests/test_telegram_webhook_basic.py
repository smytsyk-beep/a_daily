# tests/test_telegram_webhook_basic.py
from fastapi.testclient import TestClient

from app.main import app
from app.db import SessionLocal
from app import models


client = TestClient(app)


def _get_user_by_tg_id(tg_id: int) -> models.User | None:
    db = SessionLocal()
    try:
        return (
            db.query(models.User).filter(models.User.tg_user_id == str(tg_id)).first()
        )
    finally:
        db.close()


def test_telegram_webhook_start_creates_user_and_sends_welcome(monkeypatch):
    """Проверяем, что /start создаёт юзера и шлёт приветствие."""

    sent: dict = {}

    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent["chat_id"] = chat_id
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup

    # подменяем отправку сообщений, чтобы не ходить в Telegram
    monkeypatch.setattr(
        "app.routes_telegram.send_message",
        fake_send_message,
    )

    tg_id = 12345001

    update = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {
                "id": tg_id,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "chat": {"id": tg_id, "type": "private"},
            "date": 1700000000,
            "text": "/start",
        },
    }

    resp = client.post("/telegram/webhook", json=update)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # проверяем, что send_message был вызван
    assert sent["chat_id"] == tg_id
    assert "AstroDaily" in sent["text"]
    assert sent["parse_mode"] == "Markdown"

    # и что пользователь создан в БД
    user = _get_user_by_tg_id(tg_id)
    assert user is not None
    # при первом /start мы включаем доставку по умолчанию
    assert user.delivery_enabled is True


def test_telegram_webhook_today_uses_daily_digest_and_sends_buttons(monkeypatch):
    """Проверяем, что /today вызывает daily_digest и шлёт текст + inline-кнопки."""

    sent: dict = {}

    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent["chat_id"] = chat_id
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup

    monkeypatch.setattr(
        "app.routes_telegram.send_message",
        fake_send_message,
    )

    # подменяем daily_digest_module.compute, чтобы не зависеть от RAG/LLM
    def fake_compute(user_id: str, config=None):
        return [
            {
                "title": "Test digest title",
                "body": "Test digest body",
                "affirmation": "Test affirmation",
                "topic_tag": "generic_day_overview",
                "weight": 1.0,
            }
        ]

    monkeypatch.setattr(
        "app.routes_telegram.daily_digest_module.compute",
        fake_compute,
    )

    tg_id = 12345002

    # заранее создадим пользователя, чтобы не путать этот тест с /start
    db = SessionLocal()
    try:
        user = (
            db.query(models.User).filter(models.User.tg_user_id == str(tg_id)).first()
        )
        if user is None:
            user = models.User(tg_user_id=str(tg_id), locale="en")
            db.add(user)
            db.commit()
    finally:
        db.close()

    update = {
        "update_id": 2,
        "message": {
            "message_id": 2,
            "from": {
                "id": tg_id,
                "is_bot": False,
                "first_name": "Test2",
                "username": "testuser2",
            },
            "chat": {"id": tg_id, "type": "private"},
            "date": 1700000100,
            "text": "/today",
        },
    }

    resp = client.post("/telegram/webhook", json=update)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # проверяем, что пришёл наш тестовый дайджест
    assert sent["chat_id"] == tg_id
    assert "Test digest title" in sent["text"]
    assert "Test digest body" in sent["text"]
    assert "Test affirmation" in sent["text"]
    assert sent["parse_mode"] == "Markdown"

    # и что присутствуют inline-кнопки
    rm = sent["reply_markup"]
    assert isinstance(rm, dict)
    assert "inline_keyboard" in rm
    buttons = rm["inline_keyboard"][0]
    callback_data_values = {btn["callback_data"] for btn in buttons}
    assert {"dd_like", "dd_dislike", "dd_hide"} <= callback_data_values


def test_telegram_webhook_callback_feedback_ack(monkeypatch):
    """Проверяем, что callback_query с dd_like даёт корректный ответ."""

    sent: dict = {}

    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent["chat_id"] = chat_id
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup

    monkeypatch.setattr(
        "app.routes_telegram.send_message",
        fake_send_message,
    )

    tg_id = 12345003

    update = {
        "update_id": 3,
        "callback_query": {
            "id": "abc123",
            "from": {
                "id": tg_id,
                "is_bot": False,
                "first_name": "Test3",
                "username": "testuser3",
            },
            "message": {
                "message_id": 10,
                "chat": {"id": tg_id, "type": "private"},
                "date": 1700000200,
                "text": "Some previous digest text",
            },
            "data": "dd_like",
        },
    }

    resp = client.post("/telegram/webhook", json=update)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # проверяем, что бот прислал ack
    assert sent["chat_id"] == tg_id
    assert "Got it" in sent["text"]
    # parse_mode и reply_markup нам тут не важны


def test_telegram_webhook_snooze_toggles_delivery(monkeypatch):
    from app.db import SessionLocal
    from app import models

    sent: dict = {}

    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent["chat_id"] = chat_id
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup

    monkeypatch.setattr(
        "app.routes_telegram.send_message",
        fake_send_message,
    )

    tg_id = 12345004

    # создаём пользователя заранее с включённой доставкой
    db = SessionLocal()
    try:
        user = (
            db.query(models.User).filter(models.User.tg_user_id == str(tg_id)).first()
        )
        if user is None:
            user = models.User(
                tg_user_id=str(tg_id),
                locale="en",
                delivery_enabled=True,
            )
            db.add(user)
            db.commit()
        else:
            user.delivery_enabled = True
            db.commit()
    finally:
        db.close()

    # 1-й /snooze -> пауза
    update1 = {
        "update_id": 10,
        "message": {
            "message_id": 10,
            "from": {
                "id": tg_id,
                "is_bot": False,
                "first_name": "Test4",
                "username": "testuser4",
            },
            "chat": {"id": tg_id, "type": "private"},
            "date": 1700000300,
            "text": "/snooze",
        },
    }

    resp1 = client.post("/telegram/webhook", json=update1)
    assert resp1.status_code == 200
    assert resp1.json() == {"status": "ok"}

    # проверяем текст и флаг delivery_enabled=False
    assert sent["chat_id"] == tg_id
    assert "paused" in sent["text"]

    user_after_1 = _get_user_by_tg_id(tg_id)
    assert user_after_1 is not None
    assert user_after_1.delivery_enabled is False

    # 2-й /snooze -> возобновление
    update2 = {
        "update_id": 11,
        "message": {
            "message_id": 11,
            "from": {
                "id": tg_id,
                "is_bot": False,
                "first_name": "Test4",
                "username": "testuser4",
            },
            "chat": {"id": tg_id, "type": "private"},
            "date": 1700000400,
            "text": "/snooze",
        },
    }

    resp2 = client.post("/telegram/webhook", json=update2)
    assert resp2.status_code == 200
    assert resp2.json() == {"status": "ok"}

    assert sent["chat_id"] == tg_id
    assert "resumed" in sent["text"]

    user_after_2 = _get_user_by_tg_id(tg_id)
    assert user_after_2 is not None
    assert user_after_2.delivery_enabled is True
