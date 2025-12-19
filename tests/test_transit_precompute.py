# tests/test_transit_precompute.py
from datetime import date
import uuid

from app.db import SessionLocal
from app import models
from app.services.transit_events_precompute import precompute_transit_events_for_user


def _create_user(db) -> models.User:
    tg_user_id = str(uuid.uuid4())
    u = models.User(
        tg_user_id=tg_user_id,
        locale="en",
        timezone="Europe/Kyiv",
        delivery_enabled=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_birth_data(db, user_id: int) -> models.BirthData:
    bd = models.BirthData(
        user_id=user_id,
        birth_date=date(1990, 1, 1),
        birth_time="12:00",
        tz="Europe/Kyiv",
        lat=50.45,
        lon=30.523,
        place="Kyiv",
    )
    db.add(bd)
    db.commit()
    db.refresh(bd)
    return bd


def test_precompute_transit_events_writes_events_table():
    db = SessionLocal()
    try:
        user = _create_user(db)
        _create_birth_data(db, user_id=user.id)

        created = precompute_transit_events_for_user(
            db,
            user_id=user.id,
            start_local=date(2025, 1, 14),
            end_local=date(2025, 1, 15),
        )
        assert created >= 1

        rows = (
            db.query(models.Event)
            .filter(
                models.Event.user_id == user.id, models.Event.kind == "transit_aspect"
            )
            .all()
        )
        assert len(rows) >= 1
        assert rows[0].details is not None
        assert "transit_body" in rows[0].details
        assert "aspect" in rows[0].details
        assert rows[0].details["bucket"] in ("digest", "strong")
    finally:
        db.close()
