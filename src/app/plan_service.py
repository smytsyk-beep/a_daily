# src/app/plan_service.py

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from common.plans import (
    DEFAULT_PLAN,
    PlanFeature,
    PlanType,
    normalise_plan_code,
    plan_allows_feature,
    plan_max_digest_length,
)
from app import models


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_effective_plan_for_user(db: Session, user_id: int) -> PlanType:
    """
    Определяем *текущий* план юзера на основе таблицы entitlements.

    Правила:
    - Берём только записи с active = True.
    - Если expires_at не пустой и меньше now → считаем, что истекла и пропускаем.
    - Из оставшихся берём самую «свежую»:
        ORDER BY started_at DESC NULLS LAST, id DESC LIMIT 1
    - План из строки прогоняем через normalise_plan_code(...)
    - Если записей нет → DEFAULT_PLAN ("daily").
    """
    ent_q = (
        db.query(models.Entitlement)
        .filter(models.Entitlement.user_id == user_id)
        .filter(models.Entitlement.active.is_(True))
        .order_by(
            models.Entitlement.started_at.desc().nullslast(),
            models.Entitlement.id.desc(),
        )
    )

    now = _now_utc()
    for ent in ent_q:
        if ent.expires_at and ent.expires_at < now:
            # Уже истёкший entitlement — смотрим дальше.
            continue
        return normalise_plan_code(ent.plan)

    # Нет активных записей — используем неявный дефолт.
    return DEFAULT_PLAN


def user_plan_allows_feature(
    db: Session,
    user_id: int,
    feature: PlanFeature,
) -> bool:
    """
    Удобный хелпер: «есть ли у юзера право на эту фичу?».
    """
    plan = get_effective_plan_for_user(db, user_id)
    return plan_allows_feature(plan, feature)


def get_user_digest_length_cap(db: Session, user_id: int) -> str:
    """
    Максимальная длина дайджеста для юзера по его плану.

    Эту величину будем использовать как `length_override` при генерации
    дайджеста, когда будем подключать гейтинг:
    - demo → "short"
    - daily → "medium"
    - full/internal → "long"
    """
    plan = get_effective_plan_for_user(db, user_id)
    return plan_max_digest_length(plan)
