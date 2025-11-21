# tests/test_feature_flags.py
import uuid

import pytest
from sqlalchemy import insert

from app.db import SessionLocal
from app import models
from app.feature_flags import is_feature_enabled, set_user_feature


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        # если был exception, откатываемся; если нет — просто закрываем
        db.rollback()
        db.close()


def _create_test_user(db) -> models.User:
    """Создаём тестового пользователя и возвращаем объект."""
    user = models.User(
        tg_user_id=f"test_user_{uuid.uuid4().hex}",
        locale="en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_is_feature_enabled_uses_global_flag_when_no_override(db_session):
    db = db_session

    feature_key = f"test_daily_digest_{uuid.uuid4().hex}"
    user = _create_test_user(db)

    # глобальный флаг включен
    db.execute(
        insert(models.FeatureFlag).values(
            key=feature_key,
            is_enabled=True,
            payload=None,
        )
    )
    db.commit()

    # у пользователя нет override -> берём global is_enabled=True
    assert is_feature_enabled(db, user_id=user.id, feature_key=feature_key) is True


def test_is_feature_enabled_respects_user_override(db_session):
    db = db_session

    feature_key = f"test_strong_events_{uuid.uuid4().hex}"
    user = _create_test_user(db)

    # глобальный флаг выключен
    db.execute(
        insert(models.FeatureFlag).values(
            key=feature_key,
            is_enabled=False,
            payload=None,
        )
    )
    db.commit()

    # включаем фичу только для этого пользователя
    set_user_feature(db, user_id=user.id, feature_key=feature_key, enabled=True)

    assert is_feature_enabled(db, user_id=user.id, feature_key=feature_key) is True
    # для другого пользователя без override остаётся глобальный False
    other_user = _create_test_user(db)
    assert (
        is_feature_enabled(db, user_id=other_user.id, feature_key=feature_key) is False
    )
