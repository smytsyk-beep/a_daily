# tests/test_birth_data_repo.py

from datetime import date
from uuid import uuid4

import pytest

from app.db import SessionLocal
from app import repo, models


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_upsert_birth_data_sets_tz_from_coords(monkeypatch, db_session):
    db = db_session

    # делаем user_ref уникальным на каждый запуск теста
    user_ref = f"birth_user_{uuid4().hex}"

    # подменяем сервис таймзоны, чтобы не зависеть от timezonefinder
    def fake_tz_by_latlon(lat, lon):
        assert lat == 52.52
        assert lon == 13.405
        return "Europe/Berlin"

    monkeypatch.setattr(repo, "tz_by_latlon", fake_tz_by_latlon)

    bd = repo.upsert_birth_data(
        db,
        user_ref=user_ref,
        birth_date=date(1990, 1, 1),
        birth_time="10:30",
        place="Berlin",
        lat=52.52,
        lon=13.405,
        tz=None,
    )

    assert bd.id is not None
    assert bd.tz == "Europe/Berlin"

    # проверяем, что пользователь создался с правильным tg_user_id
    user = db.query(models.User).filter_by(tg_user_id=user_ref).first()
    assert user is not None
    assert user.id == bd.user_id


def test_upsert_birth_data_updates_existing(monkeypatch, db_session):
    db = db_session

    # общий user_ref для обоих вызовов, но уникальный для всего тестового прогона
    user_ref = f"same_user_{uuid4().hex}"

    monkeypatch.setattr(repo, "tz_by_latlon", lambda lat, lon: "UTC")

    # первый вызов — создаёт запись
    first = repo.upsert_birth_data(
        db,
        user_ref=user_ref,
        birth_date=date(1990, 1, 1),
        birth_time="08:00",
        place="City A",
        lat=0.0,
        lon=0.0,
        tz=None,
    )
    first_id = first.id

    # второй вызов — должен обновить существующую запись, а не создавать новую
    second = repo.upsert_birth_data(
        db,
        user_ref=user_ref,
        birth_date=date(1991, 2, 2),
        birth_time="09:30",
        place="City B",
        lat=10.0,
        lon=20.0,
        tz="Europe/Moscow",
    )

    assert second.id == first_id
    assert second.birth_date == date(1991, 2, 2)
    assert second.birth_time == "09:30"
    assert second.place == "City B"
    assert second.tz == "Europe/Moscow"
