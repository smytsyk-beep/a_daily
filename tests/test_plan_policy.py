from dataclasses import FrozenInstanceError
from inspect import getsource
from typing import get_type_hints

import pytest

import app.plan_service as legacy_plan_service
import common.entitlements as legacy_entitlements
import common.plans as plans
from common.plans import (
    DEFAULT_PLAN,
    DigestLength,
    DigestPolicy,
    PlanCode,
    PlanFeature,
    PlanRuntimeConfig,
    all_plan_codes,
    get_plan_config,
    normalize_plan_code,
    plan_allows_feature,
    resolve_digest_policy,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, PlanCode.DEMO),
        ("", PlanCode.DEMO),
        ("   ", PlanCode.DEMO),
        ("DeMo", PlanCode.DEMO),
        (" daily ", PlanCode.DAILY),
        ("FULL", PlanCode.FULL),
        ("Internal", PlanCode.INTERNAL),
        (PlanCode.FULL, PlanCode.FULL),
        ("basic", PlanCode.DAILY),
        ("pro", PlanCode.FULL),
        ("free", PlanCode.DAILY),
        ("premium", PlanCode.FULL),
        ("enterprise", PlanCode.DEMO),
    ],
)
def test_normalize_plan_code(raw, expected):
    result = normalize_plan_code(raw)

    assert result is expected
    assert isinstance(result, PlanCode)


def test_default_and_all_plan_codes_are_canonical_and_immutable():
    assert DEFAULT_PLAN is PlanCode.DEMO
    assert all_plan_codes() == frozenset(PlanCode)
    assert isinstance(all_plan_codes(), frozenset)


@pytest.mark.parametrize(
    ("plan_code", "max_length", "atom_cap", "features"),
    [
        (
            PlanCode.DEMO,
            DigestLength.SHORT,
            2,
            frozenset({PlanFeature.DAILY_DIGEST}),
        ),
        (
            PlanCode.DAILY,
            DigestLength.MEDIUM,
            3,
            frozenset({PlanFeature.DAILY_DIGEST, PlanFeature.QUIET_MODE}),
        ),
        (
            PlanCode.FULL,
            DigestLength.LONG,
            6,
            frozenset(PlanFeature),
        ),
        (
            PlanCode.INTERNAL,
            DigestLength.LONG,
            6,
            frozenset(PlanFeature),
        ),
    ],
)
def test_plan_runtime_config_matrix(plan_code, max_length, atom_cap, features):
    config = get_plan_config(plan_code)

    assert isinstance(config, PlanRuntimeConfig)
    assert config.code is plan_code
    assert config.max_digest_length is max_length
    assert config.digest_cap is max_length
    assert config.atom_cap == atom_cap
    assert config.features == features
    assert isinstance(config.features, frozenset)


def test_runtime_config_is_frozen_and_not_a_plan_string():
    config = get_plan_config(PlanCode.DAILY)

    with pytest.raises(FrozenInstanceError):
        config.atom_cap = 99
    with pytest.raises(AttributeError):
        config.features.add(PlanFeature.CALENDAR_ICS)
    assert config != PlanCode.DAILY
    assert config != "daily"


@pytest.mark.parametrize(
    ("plan_code", "requested", "final_length", "atom_cap"),
    [
        ("demo", "short", DigestLength.SHORT, 2),
        ("demo", "medium", DigestLength.SHORT, 2),
        ("demo", "long", DigestLength.SHORT, 2),
        ("daily", "short", DigestLength.SHORT, 2),
        ("daily", "medium", DigestLength.MEDIUM, 3),
        ("daily", "long", DigestLength.MEDIUM, 3),
        ("full", "short", DigestLength.SHORT, 2),
        ("full", "medium", DigestLength.MEDIUM, 3),
        ("full", "long", DigestLength.LONG, 6),
        ("internal", "short", DigestLength.SHORT, 2),
        ("internal", "medium", DigestLength.MEDIUM, 3),
        ("internal", "long", DigestLength.LONG, 6),
    ],
)
def test_digest_policy_matrix(plan_code, requested, final_length, atom_cap):
    policy = resolve_digest_policy(plan_code, requested)

    assert isinstance(policy, DigestPolicy)
    assert policy.plan_code is PlanCode(plan_code)
    assert policy.requested_length is DigestLength(requested)
    assert policy.final_length is final_length
    assert policy.atom_cap == atom_cap


@pytest.mark.parametrize("requested", [None, "", "unsupported", "   "])
def test_unsupported_requested_length_fails_safe_to_short(requested):
    policy = resolve_digest_policy(PlanCode.INTERNAL, requested)

    assert policy.requested_length is DigestLength.SHORT
    assert policy.final_length is DigestLength.SHORT
    assert policy.atom_cap == 2


def test_digest_policy_is_frozen():
    policy = resolve_digest_policy(PlanCode.FULL, DigestLength.LONG)

    with pytest.raises(FrozenInstanceError):
        policy.atom_cap = 2


@pytest.mark.parametrize(
    ("plan_code", "allowed"),
    [
        (PlanCode.DEMO, {PlanFeature.DAILY_DIGEST}),
        (
            PlanCode.DAILY,
            {PlanFeature.DAILY_DIGEST, PlanFeature.QUIET_MODE},
        ),
        (PlanCode.FULL, set(PlanFeature)),
        (PlanCode.INTERNAL, set(PlanFeature)),
    ],
)
def test_feature_matrix(plan_code, allowed):
    for feature in PlanFeature:
        assert plan_allows_feature(plan_code, feature) is (feature in allowed)


@pytest.mark.parametrize("feature", ["", "unknown", "calendar", "billing"])
def test_unknown_features_fail_closed(feature):
    assert plan_allows_feature(PlanCode.INTERNAL, feature) is False


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("basic", PlanCode.DAILY),
        ("pro", PlanCode.FULL),
        ("free", PlanCode.DAILY),
        ("premium", PlanCode.FULL),
    ],
)
def test_plan_aliases_share_the_canonical_feature_matrix(alias, canonical):
    for feature in PlanFeature:
        assert plan_allows_feature(alias, feature) is plan_allows_feature(
            canonical, feature
        )


def test_canonical_public_api_return_annotations_are_distinct():
    assert get_type_hints(plans.get_user_plan_code)["return"] is PlanCode
    assert get_type_hints(plans.get_plan_config)["return"] is PlanRuntimeConfig
    assert get_type_hints(plans.get_user_plan_config)["return"] is PlanRuntimeConfig
    assert get_type_hints(plans.resolve_digest_policy)["return"] is DigestPolicy
    assert get_type_hints(plans.get_user_plan)["return"] is PlanCode


def test_plan_code_has_no_runtime_config_code_attribute():
    plan_code = normalize_plan_code("daily")

    with pytest.raises(AttributeError):
        _ = plan_code.code


def test_compatibility_helpers_delegate_to_canonical_policy(monkeypatch):
    sentinel = get_plan_config(PlanCode.INTERNAL)
    monkeypatch.setattr(plans, "get_plan_config", lambda _code: sentinel)

    assert plans.get_plan_runtime_config("demo") is sentinel
    assert plans.plan_max_digest_length("demo") is DigestLength.LONG


def test_duplicate_modules_own_no_plan_matrix_or_entitlement_query():
    for module in (legacy_entitlements, legacy_plan_service):
        source = getsource(module)
        assert "SELECT plan" not in source
        assert "_PLAN_CONFIGS" not in source
