# tests/test_natal_cache_behavior.py
from datetime import date
from unittest.mock import patch
import uuid

from app.db import SessionLocal
from app import models
from app.astro.natal import get_or_compute_natal


def _create_user(db, locale: str = "en", timezone: str = "Europe/Kyiv") -> models.User:
    # уникальный tg_user_id на каждый запуск тестов
    tg_user_id = uuid.uuid4().int % 2_000_000_000

    u = models.User(
        tg_user_id=tg_user_id,
        locale=locale,
        timezone=timezone,
        delivery_enabled=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_birth_data(db, user_id: int):
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


def test_natal_creates_cache_record():
    db = SessionLocal()
    try:
        user = _create_user(db)
        birth = _create_birth_data(db, user_id=user.id)

        chart = get_or_compute_natal(db, birth)
        assert "sun" in chart.bodies

        cache = (
            db.query(models.NatalCache)
            .filter(models.NatalCache.user_id == user.id)
            .first()
        )
        assert cache is not None
    finally:
        db.close()


def test_natal_uses_cache_without_recalc():
    db = SessionLocal()
    try:
        user = _create_user(db)
        birth = _create_birth_data(db, user_id=user.id)

        # прогрев кэша
        get_or_compute_natal(db, birth)

        # повторный вызов: кэш без пересчёта
        with patch("app.astro.natal.compute_all_bodies") as mocked:
            chart2 = get_or_compute_natal(db, birth)
            mocked.assert_not_called()
            assert "moon" in chart2.bodies
    finally:
        db.close()
