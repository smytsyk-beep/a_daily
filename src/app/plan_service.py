"""Deprecated plan-service compatibility API.

Canonical plan policy lives in :mod:`common.plans`.  These names remain until
Issue #42 migrates their callers; this module owns no matrix or entitlement
query.
"""

from sqlalchemy.orm import Session

from common.plans import (
    DigestLength,
    PlanCode,
    PlanFeature,
    get_user_plan_code,
    plan_allows_feature,
    plan_max_digest_length,
)


def get_effective_plan_for_user(db: Session, user_id: int) -> PlanCode:
    """Deprecated wrapper for :func:`common.plans.get_user_plan_code`."""

    return get_user_plan_code(db, user_id)


def user_plan_allows_feature(
    db: Session,
    user_id: int,
    feature: PlanFeature,
) -> bool:
    """Deprecated wrapper for the canonical feature policy."""

    return plan_allows_feature(get_user_plan_code(db, user_id), feature)


def get_user_digest_length_cap(db: Session, user_id: int) -> DigestLength:
    """Deprecated wrapper for the canonical plan maximum."""

    return plan_max_digest_length(get_user_plan_code(db, user_id))
