# src/app/feature_flags.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models import FeatureFlag, UserFeatureFlag, Entitlement


def is_feature_enabled(db: Session, user_id: int, feature_key: str) -> bool:
    """
    Проверяем, включена ли фича feature_key для user_id.

    Логика:
      1) Если есть override в user_feature_flags → возвращаем его.
      2) Иначе смотрим глобальный FeatureFlag.key == feature_key.
      3) Если глобального флага нет → считаем фичу выключенной.
    """

    # 1. override для конкретного пользователя
    stmt_override = select(UserFeatureFlag).where(
        UserFeatureFlag.user_id == user_id,
        UserFeatureFlag.feature_key == feature_key,
    )
    override = db.execute(stmt_override).scalar_one_or_none()
    if override is not None:
        return bool(override.enabled)

    # 2. глобальный флаг
    ff = db.get(FeatureFlag, feature_key)  # PK = key
    if ff is None:
        return False

    return bool(ff.is_enabled)


def set_user_feature(
    db: Session,
    user_id: int,
    feature_key: str,
    enabled: bool,
) -> UserFeatureFlag:
    """
    Установить/обновить override для пользователя.
    Возвращает объект UserFeatureFlag.
    """
    stmt = select(UserFeatureFlag).where(
        UserFeatureFlag.user_id == user_id,
        UserFeatureFlag.feature_key == feature_key,
    )
    uff = db.execute(stmt).scalar_one_or_none()

    if uff is None:
        uff = UserFeatureFlag(
            user_id=user_id,
            feature_key=feature_key,
            enabled=enabled,
        )
        db.add(uff)
    else:
        uff.enabled = enabled

    db.commit()
    db.refresh(uff)
    return uff


def get_user_active_plan(db: Session, user_id: int) -> Optional[str]:
    """
    Возвращает активный план пользователя (Entitlement.plan),
    если он есть. Если нет активных планов — None.
    """
    ent = (
        db.query(Entitlement)
        .filter(Entitlement.user_id == user_id, Entitlement.active.is_(True))
        .order_by(Entitlement.started_at.desc())
        .first()
    )
    if not ent:
        return None
    return ent.plan


def is_module_enabled_for_user_and_plan(
    db: Session,
    module_name: str,
    user_id: int,
) -> bool:
    """
    Высокоуровневая проверка доступности модуля для пользователя:

    1) Берём FeatureFlag с ключом `module:{module_name}`.
       - если флаг не найден → модуль считается включённым.
       - если флаг найден, берём flag.is_enabled как базовое состояние.

    2) Смотрим UserFeatureFlag по (user_id, feature_key).
       - если есть запись, её enabled перекрывает глобальный флаг.

    3) Если после override модуль выключен → сразу False.

    4) Если в FeatureFlag.payload есть поле "plans" (список строк),
       то модуль доступен только для пользователей с активным планом из этого списка.
       План берём из Entitlement (get_user_active_plan).

       - если "plans" не задано → план не учитывается (модуль открыт для всех).
       - если "plans" задан, но у пользователя нет активного плана → модуль выключен.
    """

    feature_key = f"module:{module_name}"

    # 1. глобальный флаг
    flag: FeatureFlag | None = db.get(FeatureFlag, feature_key)
    enabled = True  # по умолчанию модуль включён

    if flag is not None:
        enabled = bool(flag.is_enabled)

    # 2. override на пользователя
    uf = (
        db.query(UserFeatureFlag)
        .filter(
            UserFeatureFlag.user_id == user_id,
            UserFeatureFlag.feature_key == feature_key,
        )
        .first()
    )
    if uf is not None:
        enabled = bool(uf.enabled)

    if not enabled:
        return False

    # 3. проверка плана, если payload.plans задан
    if not flag or not flag.payload:
        return True

    payload = flag.payload or {}
    plans = payload.get("plans")
    if not plans:
        # нет ограничений по планам
        return True

    user_plan = get_user_active_plan(db, user_id)
    if user_plan is None:
        # есть ограничения по плану, но план не найден → отключаем
        return False

    return user_plan in plans


__all__ = [
    "is_feature_enabled",
    "set_user_feature",
    "get_user_active_plan",
    "is_module_enabled_for_user_and_plan",
]
