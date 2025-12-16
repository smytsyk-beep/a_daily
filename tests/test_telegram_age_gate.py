# tests/test_telegram_age_gate.py

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_start_message_contains_age_gate_and_disclaimer(monkeypatch):
    sent = {}

    def fake_send_message(chat_id, text, parse_mode=None, reply_markup=None):
        sent["chat_id"] = chat_id
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup
        return {"ok": True}

    # подменяем send_message в routes_telegram
    monkeypatch.setattr(
        "app.routes_telegram.send_message",
        fake_send_message,
    )

    payload = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": int(datetime.utcnow().timestamp()),
            "chat": {"id": 123, "type": "private"},
            "from": {
                "id": 123,
                "is_bot": False,
                "first_name": "Test",
            },
            "text": "/start",
        },
    }

    resp = client.post("/telegram/webhook", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    text = sent.get("text", "")
    # проверяем, что ключевые фразы действительно есть
    assert "18+" in text
    assert "entertainment purposes only" in text
    assert "medical" in text or "financial" in text or "legal" in text
