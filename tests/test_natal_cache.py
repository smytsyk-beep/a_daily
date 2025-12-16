# tests/test_natal_cache.py

from datetime import date
from typing import Any, Dict

import pytest
from app.db import SessionLocal

from app import models
from app.repo import upsert_birth_data
from app.astro_core import get_or_compute_natal
from app.astro import skyfield_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_user(db):
    # пробуем найти существующего пользователя с тем же tg_user_id
    user = db.query(models.User).filter(models.User.tg_user_id == "natal_user").first()
    if user is not None:
        return user

    # если нет — создаём
    user = models.User(tg_user_id="natal_user", locale="en")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_or_compute_natal_creates_cache_and_uses_skyfield(monkeypatch, db_session):
    db = db_session
    user = _make_user(db)

    # birth_data с координатами
    upsert_birth_data(
        db,
        user_id=user.id,
        birth_date=date(1990, 1, 1),
        birth_time="12:00",
        place="Test City",
        lat=10.0,
        lon=20.0,
    )

    # подменяем skyfield_client.compute_all_bodies простой заглушкой
    calls: Dict[str, Any] = {}

    def fake_compute_all_bodies(dt_utc, lat, lon):
        calls["called"] = True
        return {
            "sun": skyfield_client.BodyPosition(
                body="sun",
                lon=10.0,
                lat=0.0,
                distance_au=1.0,
                sign="Aries",
                sign_degree=10.0,
            )
        }

    monkeypatch.setattr(
        "app.astro.skyfield_client.compute_all_bodies", fake_compute_all_bodies
    )

    payload = get_or_compute_natal(db, user.id, recalc=True)

    assert calls.get("called") is True
    assert "bodies" in payload
    assert payload["bodies"]["sun"]["sign"] == "Aries"

    # проверяем, что запись в NatalCache появилась
    cached = (
        db.query(models.NatalCache).filter(models.NatalCache.user_id == user.id).one()
    )
    assert cached.payload["bodies"]["sun"]["sign"] == "Aries"


def test_get_or_compute_natal_uses_cache_without_recalc(monkeypatch, db_session):
    db = db_session
    user = _make_user(db)

    # birth_data — как и в предыдущем тесте
    upsert_birth_data(
        db,
        user_id=user.id,
        birth_date=date(1990, 1, 1),
        birth_time="12:00",
        place="Test City",
        lat=10.0,
        lon=20.0,
    )

    # 1-й вызов — создаём кэш
    def first_compute_all_bodies(dt_utc, lat, lon):
        return {
            "sun": skyfield_client.BodyPosition(
                body="sun",
                lon=10.0,
                lat=0.0,
                distance_au=1.0,
                sign="Aries",
                sign_degree=10.0,
            )
        }

    monkeypatch.setattr(
        "app.astro.skyfield_client.compute_all_bodies", first_compute_all_bodies
    )
    get_or_compute_natal(db, user.id, recalc=True)

    # 2-й вызов — подменяем функцию тем, что бросает исключение.
    # Если кэш используется, она вызываться не должна.
    def exploding_compute_all_bodies(*args, **kwargs):
        raise AssertionError(
            "compute_all_bodies should not be called when cache exists"
        )

    monkeypatch.setattr(
        "app.astro.skyfield_client.compute_all_bodies",
        exploding_compute_all_bodies,
    )

    payload = get_or_compute_natal(db, user.id, recalc=False)

    assert payload["bodies"]["sun"]["sign"] == "Aries"
