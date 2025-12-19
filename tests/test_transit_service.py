# tests/test_transit_service.py
from datetime import date
import uuid

from app.db import SessionLocal
from app import models
from app.astro.transit_service import (
    compute_daily_digest_transits,
    compute_strong_alert_transits,
)


def _create_user(db) -> models.User:
    tg_user_id = uuid.uuid4().int % 2_000_000_000
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
    )
    db.add(bd)
    db.commit()
    db.refresh(bd)
    return bd


def test_transits_digest_and_strong_alerts_run_and_are_stable_enough():
    db = SessionLocal()
    try:
        user = _create_user(db)
        _create_birth_data(db, user_id=user.id)

        d = date(2025, 1, 15)

        digest_events = compute_daily_digest_transits(db, user_id=user.id, local_date=d)
        strong_events = compute_strong_alert_transits(db, user_id=user.id, local_date=d)

        # Минимальные проверки (без “golden” на аспекты — пока):
        assert isinstance(digest_events, list)
        assert isinstance(strong_events, list)

        # обычно хотя бы что-то находится на орбе 2°
        assert len(digest_events) >= 1

        # strong может быть пустым — это нормально, но структура должна быть корректной
        if strong_events:
            e = strong_events[0]
            assert e.kind == "transit_aspect"
            assert e.orb_deg <= 1.0
    finally:
        db.close()
