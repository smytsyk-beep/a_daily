# tests/test_user_summary_api.py

from datetime import date, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.db import SessionLocal
from app import models

client = TestClient(app)


def _create_user(db, tg_user_id: str = "summary_user") -> models.User:
    """
    Идempotent-хелпер:
    - если пользователь с таким tg_user_id уже есть — обновляем ключевые поля и возвращаем;
    - если нет — создаём нового.
    """
    user = db.query(models.User).filter_by(tg_user_id=tg_user_id).first()

    if user is None:
        user = models.User(
            tg_user_id=tg_user_id,
            locale="en",
            timezone="Europe/Berlin",
            display_name="Summary User",
            digest_interests=["work", "love"],
            digest_length_preference="medium",
            delivery_time_local="09:00",
            delivery_enabled=True,
            quiet_mode=False,
        )
        db.add(user)
    else:
        # Обновляем поля, чтобы состояние было предсказуемым для теста
        user.locale = "en"
        user.timezone = "Europe/Berlin"
        user.display_name = "Summary User"
        user.digest_interests = ["work", "love"]
        user.digest_length_preference = "medium"
        user.delivery_time_local = "09:00"
        user.delivery_enabled = True
        user.quiet_mode = False

    db.commit()
    db.refresh(user)
    return user


def _create_birth_data(db, user: models.User) -> models.BirthData:
    bd = models.BirthData(
        user_id=user.id,
        birth_date=date(1990, 1, 1),
        birth_time="10:30",
        tz="Europe/Berlin",
        place="Berlin",
        lat=52.52,
        lon=13.405,
    )
    db.add(bd)
    db.commit()
    db.refresh(bd)
    return bd


def _create_entitlement(db, user: models.User) -> models.Entitlement:
    ent = models.Entitlement(
        user_id=user.id,
        plan="basic",
        active=True,
        started_at=datetime(2025, 1, 1, 0, 0, 0),
        expires_at=datetime(2025, 12, 31, 23, 59, 59),
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def test_user_summary_returns_aggregated_blocks():
    db = SessionLocal()
    try:
        user = _create_user(db, tg_user_id="summary_user_full")
        bd = _create_birth_data(db, user)
        ent = _create_entitlement(db, user)

        # Сохраняем значения до закрытия сессии
        user_id = user.id
        tg_user_id = user.tg_user_id

        bd_birth_date = bd.birth_date
        bd_birth_time = bd.birth_time
        bd_tz = bd.tz

        ent_plan = ent.plan
        ent_active = ent.active
    finally:
        db.close()

    resp = client.get("/user/summary", params={"user_ref": tg_user_id})
    assert resp.status_code == 200

    data = resp.json()
    user_block = data["user"]
    birth_block = data["birth_data"]
    ent_block = data["entitlement"]

    # user
    assert user_block["id"] == user_id
    assert user_block["tg_user_id"] == tg_user_id
    assert user_block["locale"] == "en"
    assert user_block["delivery"]["time_local"] == "09:00"
    assert user_block["delivery"]["enabled"] is True

    # birth_data
    assert birth_block["has_birth_data"] is True
    assert birth_block["birth_date"] == bd_birth_date.isoformat()
    assert birth_block["birth_time"] == bd_birth_time
    assert birth_block["tz"] == bd_tz

    # entitlement
    assert ent_block is not None
    assert ent_block["plan"] == ent_plan
    assert ent_block["active"] is ent_active


def test_user_summary_when_no_birthdata_or_entitlement():
    db = SessionLocal()
    try:
        user = _create_user(db, tg_user_id="summary_user_empty")
        tg_user_id = user.tg_user_id
    finally:
        db.close()

    resp = client.get("/user/summary", params={"user_ref": tg_user_id})
    assert resp.status_code == 200

    data = resp.json()
    birth_block = data["birth_data"]
    ent_block = data["entitlement"]

    assert birth_block["has_birth_data"] is False
    assert ent_block is None


def test_user_summary_returns_404_for_unknown_user():
    resp = client.get("/user/summary", params={"user_ref": "unknown_user_123456"})
    assert resp.status_code == 404
