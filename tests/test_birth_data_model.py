# tests/test_birth_data_model.py

from datetime import date
from uuid import uuid4

from app.db import SessionLocal
from app import models


def test_birth_data_roundtrip_matches_model_and_db():
    db = SessionLocal()
    try:
        # уникальный tg_user_id для каждого запуска теста
        tg_id = f"birthdata_test_user_{uuid4().hex}"

        user = models.User(
            tg_user_id=tg_id,
            locale="en",
        )
        db.add(user)
        db.flush()  # получаем user.id без commit
        assert user.id is not None

        bd = models.BirthData(
            user_id=user.id,
            birth_date=date(1990, 1, 1),
            birth_time="12:00",
            tz="Europe/Kyiv",
            place="Kyiv, Ukraine",
            lat=50.45,
            lon=30.52,
        )
        db.add(bd)
        db.flush()  # получаем bd.id
        assert bd.id is not None

        # читаем обратно из БД и сверяем поля
        row = db.query(models.BirthData).filter_by(id=bd.id).one()

        assert row.user_id == user.id
        assert row.birth_date == date(1990, 1, 1)
        assert row.birth_time == "12:00"
        assert row.tz == "Europe/Kyiv"
        assert row.place == "Kyiv, Ukraine"
        assert row.lat == 50.45
        assert row.lon == 30.52
    finally:
        # откатываем транзакцию — тест не оставляет данные
        db.rollback()
        db.close()
