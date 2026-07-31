from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app import models
from app.db import SessionLocal
from app.plan_service import get_effective_plan_for_user
from common.entitlements import get_active_plan_code
from common.plans import (
    DigestLength,
    PlanCode,
    PlanRuntimeConfig,
    get_plan_runtime_config_for_user,
    get_user_plan,
    get_user_plan_code,
    get_user_plan_config,
    is_feature_allowed_for_user,
    PlanFeature,
)


NOW = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _make_user(db) -> models.User:
    user = models.User(tg_user_id=f"plan-policy-{uuid.uuid4().hex}", locale="en")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_entitlement(
    db,
    user_id: int,
    *,
    plan: str,
    active: bool = True,
    started_at: datetime = NOW - timedelta(days=1),
    expires_at: datetime | None = None,
) -> models.Entitlement:
    entitlement = models.Entitlement(
        user_id=user_id,
        plan=plan,
        active=active,
        started_at=_naive_utc(started_at),
        expires_at=_naive_utc(expires_at) if expires_at else None,
    )
    db.add(entitlement)
    db.commit()
    db.refresh(entitlement)
    return entitlement


def test_no_entitlement_returns_demo_plan_code():
    with SessionLocal() as db:
        user = _make_user(db)

        result = get_user_plan_code(db, user.id, now=NOW)

        assert result is PlanCode.DEMO
        assert isinstance(result, PlanCode)


@pytest.mark.parametrize("plan_code", list(PlanCode))
def test_active_canonical_entitlement_returns_plan(plan_code):
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan=plan_code.value)

        assert get_user_plan_code(db, user.id, now=NOW) is plan_code


def test_future_entitlement_returns_demo():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(
            db,
            user.id,
            plan="full",
            started_at=NOW + timedelta(seconds=1),
        )

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


def test_entitlement_expiring_in_future_is_effective():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(
            db,
            user.id,
            plan="full",
            expires_at=NOW + timedelta(seconds=1),
        )

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.FULL


def test_expired_entitlement_returns_demo():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(
            db,
            user.id,
            plan="full",
            expires_at=NOW - timedelta(seconds=1),
        )

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


def test_entitlement_expiring_exactly_now_is_not_effective():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="full", expires_at=NOW)

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


def test_entitlement_starting_exactly_now_is_effective():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="daily", started_at=NOW)

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DAILY


def test_inactive_entitlement_returns_demo():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="full", active=False)

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


def test_unknown_entitlement_value_returns_demo():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="enterprise")

        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("basic", PlanCode.DAILY),
        ("pro", PlanCode.FULL),
        ("free", PlanCode.DAILY),
        ("premium", PlanCode.FULL),
    ],
)
def test_legacy_entitlement_aliases_are_normalized(alias, expected):
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan=alias)

        assert get_user_plan_code(db, user.id, now=NOW) is expected


def test_multiple_effective_rows_resolve_deterministically_and_fail_closed():
    with SessionLocal() as db:
        user = _make_user(db)
        same_start = NOW - timedelta(days=1)
        known = _add_entitlement(
            db,
            user.id,
            plan="full",
            started_at=same_start,
        )
        unknown = _add_entitlement(
            db,
            user.id,
            plan="enterprise",
            started_at=same_start,
        )

        assert unknown.id > known.id
        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DEMO


def test_explicit_now_controls_entitlement_boundary():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="daily", started_at=NOW)

        assert (
            get_user_plan_code(db, user.id, now=NOW - timedelta(seconds=1))
            is PlanCode.DEMO
        )
        assert get_user_plan_code(db, user.id, now=NOW) is PlanCode.DAILY


def test_aware_non_utc_now_is_converted_to_the_same_utc_instant():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="daily", started_at=NOW)
        istanbul_now = NOW.astimezone(timezone(timedelta(hours=3)))

        assert get_user_plan_code(db, user.id, now=istanbul_now) is PlanCode.DAILY


def test_naive_now_is_rejected_explicitly():
    with SessionLocal() as db:
        user = _make_user(db)

        with pytest.raises(ValueError, match="timezone-aware"):
            get_user_plan_code(db, user.id, now=NOW.replace(tzinfo=None))


def test_user_config_and_compatibility_helpers_return_unambiguous_types():
    with SessionLocal() as db:
        user = _make_user(db)
        _add_entitlement(db, user.id, plan="daily")

        config = get_user_plan_config(db, user.id, now=NOW)
        legacy_config = get_plan_runtime_config_for_user(db, user.id, now=NOW)

        assert isinstance(config, PlanRuntimeConfig)
        assert config.code is PlanCode.DAILY
        assert config.max_digest_length is DigestLength.MEDIUM
        assert legacy_config is config
        assert get_user_plan(db, user.id, now=NOW) is PlanCode.DAILY
        assert get_active_plan_code(db, user.id, NOW) is PlanCode.DAILY
        assert get_effective_plan_for_user(db, user.id) is PlanCode.DAILY
        assert (
            is_feature_allowed_for_user(
                db,
                user.id,
                PlanFeature.STRONG_ALERTS,
                now=NOW,
            )
            is False
        )
