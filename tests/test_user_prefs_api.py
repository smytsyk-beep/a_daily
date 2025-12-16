# tests/test_user_prefs_api.py

from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.db import SessionLocal
from app import models

client = TestClient(app)


def _create_user(locale: str = "en") -> int:
    db = SessionLocal()
    try:
        tg_uid = f"prefs_test_{uuid.uuid4()}"
        user = models.User(
            tg_user_id=tg_uid,
            locale=locale,
            # остальные поля пусть будут по умолчанию
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def test_get_user_prefs_returns_defaults_for_new_user():
    user_id = _create_user()

    resp = client.get(f"/users/{user_id}/prefs")
    assert resp.status_code == 200

    data = resp.json()
    assert data["user_id"] == user_id
    assert data["locale"] == "en"
    # по умолчанию interests -> ["general"]
    assert data["interests"] == ["general"]
    assert data["preferred_length"] == "medium"
    # delivery_enabled по умолчанию True, если None
    assert data["delivery_enabled"] is True


def test_patch_user_prefs_updates_fields_and_persists():
    user_id = _create_user()

    payload = {
        "locale": "ru",
        "interests": ["work", "love"],
        "preferred_length": "long",
        "delivery_enabled": False,
        "time_local": "21:00",
    }

    resp = client.patch(f"/users/{user_id}/prefs", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["user_id"] == user_id
    assert data["locale"] == "ru"
    assert data["interests"] == ["work", "love"]
    assert data["preferred_length"] == "long"
    assert data["delivery_enabled"] is False
    assert data["time_local"] == "21:00"

    # второй запрос GET должен вернуть те же значения
    resp2 = client.get(f"/users/{user_id}/prefs")
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data2 == data
