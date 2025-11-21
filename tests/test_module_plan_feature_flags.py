import uuid

from app.db import SessionLocal
from app import models
from app.feature_flags import (
    get_user_active_plan,
    is_module_enabled_for_user_and_plan,
)


def _make_user(db) -> models.User:
    alias = f"plan_user_{uuid.uuid4().hex}"
    user = models.User(tg_user_id=alias, locale="en")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_user_active_plan_picks_latest_active():
    db = SessionLocal()
    try:
        user = _make_user(db)

        db.add(
            models.Entitlement(
                user_id=user.id,
                plan="basic",
                active=True,
            )
        )
        db.commit()

        assert get_user_active_plan(db, user.id) == "basic"

        # помечаем старый как неактивный, добавляем pro
        db.query(models.Entitlement).filter_by(user_id=user.id).update(
            {"active": False}
        )
        db.add(
            models.Entitlement(
                user_id=user.id,
                plan="pro",
                active=True,
            )
        )
        db.commit()

        assert get_user_active_plan(db, user.id) == "pro"
    finally:
        db.close()


def test_module_plan_restriction_basic():
    db = SessionLocal()
    try:
        user = _make_user(db)

        # активный план basic
        db.add(
            models.Entitlement(
                user_id=user.id,
                plan="basic",
                active=True,
            )
        )
        db.commit()

        module_name = f"pro_module_{uuid.uuid4().hex}"
        feature_key = f"module:{module_name}"

        # модуль включён глобально, но только для plans=["pro"]
        db.add(
            models.FeatureFlag(
                key=feature_key,
                is_enabled=True,
                payload={"plans": ["pro"]},
            )
        )
        db.commit()

        # c basic-планом модуль не доступен
        assert is_module_enabled_for_user_and_plan(db, module_name, user.id) is False

        # переключаем план на pro
        db.query(models.Entitlement).filter_by(user_id=user.id).update(
            {"active": False}
        )
        db.add(
            models.Entitlement(
                user_id=user.id,
                plan="pro",
                active=True,
            )
        )
        db.commit()

        assert is_module_enabled_for_user_and_plan(db, module_name, user.id) is True
    finally:
        db.close()


def test_module_without_flag_is_enabled_for_any_plan():
    db = SessionLocal()
    try:
        user = _make_user(db)

        db.add(
            models.Entitlement(
                user_id=user.id,
                plan="basic",
                active=True,
            )
        )
        db.commit()

        # нет FeatureFlag для такого модуля → должен быть разрешён
        assert (
            is_module_enabled_for_user_and_plan(db, "nonexistent_module", user.id)
            is True
        )
    finally:
        db.close()
