"""Canonical, channel-neutral plan and digest policy.

The entitlement timestamps in the current schema are PostgreSQL
``timestamp without time zone`` values.  This module treats those stored
values as UTC at the repository boundary.  Public APIs accept only aware
``now`` values so a server-local timezone can never be inferred implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Final, FrozenSet, Mapping, TypeAlias

from sqlalchemy import text
from sqlalchemy.orm import Session


class PlanCode(StrEnum):
    """Canonical plan identifiers persisted and used by policy."""

    DEMO = "demo"
    DAILY = "daily"
    FULL = "full"
    INTERNAL = "internal"


class DigestLength(StrEnum):
    """Canonical requested and resolved digest lengths."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class PlanFeature(StrEnum):
    """Canonical plan-gated feature identifiers."""

    DAILY_DIGEST = "daily_digest"
    STRONG_ALERTS = "strong_alerts"
    CALENDAR_ICS = "calendar_ics"
    QUIET_MODE = "quiet_mode"

    # Compatibility alias used by existing callers and translations.
    ALERTS_STRONG = "strong_alerts"


@dataclass(frozen=True)
class PlanRuntimeConfig:
    """Immutable maximum capabilities for one canonical plan."""

    code: PlanCode
    max_digest_length: DigestLength
    atom_cap: int
    features: FrozenSet[PlanFeature]

    @property
    def digest_cap(self) -> DigestLength:
        """Deprecated compatibility name; use ``max_digest_length``."""

        return self.max_digest_length


@dataclass(frozen=True)
class DigestPolicy:
    """Immutable resolved digest policy for a plan and user preference."""

    plan_code: PlanCode
    requested_length: DigestLength
    final_length: DigestLength
    atom_cap: int


DEFAULT_PLAN: Final[PlanCode] = PlanCode.DEMO
DEFAULT_PLAN_CODE: Final[PlanCode] = DEFAULT_PLAN

_PLAN_ALIASES: Final[Mapping[str, PlanCode]] = MappingProxyType(
    {
        "basic": PlanCode.DAILY,
        "pro": PlanCode.FULL,
        "free": PlanCode.DAILY,
        "premium": PlanCode.FULL,
    }
)

_ATOM_CAPS: Final[Mapping[DigestLength, int]] = MappingProxyType(
    {
        DigestLength.SHORT: 2,
        DigestLength.MEDIUM: 3,
        DigestLength.LONG: 6,
    }
)

_PLAN_CONFIGS: Final[Mapping[PlanCode, PlanRuntimeConfig]] = MappingProxyType(
    {
        PlanCode.DEMO: PlanRuntimeConfig(
            code=PlanCode.DEMO,
            max_digest_length=DigestLength.SHORT,
            atom_cap=2,
            features=frozenset({PlanFeature.DAILY_DIGEST}),
        ),
        PlanCode.DAILY: PlanRuntimeConfig(
            code=PlanCode.DAILY,
            max_digest_length=DigestLength.MEDIUM,
            atom_cap=3,
            features=frozenset({PlanFeature.DAILY_DIGEST, PlanFeature.QUIET_MODE}),
        ),
        PlanCode.FULL: PlanRuntimeConfig(
            code=PlanCode.FULL,
            max_digest_length=DigestLength.LONG,
            atom_cap=6,
            features=frozenset(
                {
                    PlanFeature.DAILY_DIGEST,
                    PlanFeature.QUIET_MODE,
                    PlanFeature.STRONG_ALERTS,
                    PlanFeature.CALENDAR_ICS,
                }
            ),
        ),
        PlanCode.INTERNAL: PlanRuntimeConfig(
            code=PlanCode.INTERNAL,
            max_digest_length=DigestLength.LONG,
            atom_cap=6,
            features=frozenset(
                {
                    PlanFeature.DAILY_DIGEST,
                    PlanFeature.QUIET_MODE,
                    PlanFeature.STRONG_ALERTS,
                    PlanFeature.CALENDAR_ICS,
                }
            ),
        ),
    }
)

_LENGTH_ORDER: Final[Mapping[DigestLength, int]] = MappingProxyType(
    {
        DigestLength.SHORT: 0,
        DigestLength.MEDIUM: 1,
        DigestLength.LONG: 2,
    }
)

_FEATURE_ALIASES: Final[Mapping[str, PlanFeature]] = MappingProxyType(
    {
        "daily_digest": PlanFeature.DAILY_DIGEST,
        "digest_daily": PlanFeature.DAILY_DIGEST,
        "digest_daily_demo": PlanFeature.DAILY_DIGEST,
        "strong_alerts": PlanFeature.STRONG_ALERTS,
        "alerts_strong": PlanFeature.STRONG_ALERTS,
        "calendar_ics": PlanFeature.CALENDAR_ICS,
        "quiet_mode": PlanFeature.QUIET_MODE,
    }
)


def all_plan_codes() -> FrozenSet[PlanCode]:
    """Return the immutable set of canonical plan identifiers."""

    return frozenset(_PLAN_CONFIGS)


def normalize_plan_code(raw: str | PlanCode | None) -> PlanCode:
    """Normalize canonical codes and legacy aliases, failing safe to demo."""

    if isinstance(raw, PlanCode):
        return raw
    if raw is None:
        return DEFAULT_PLAN

    value = str(raw).strip().lower()
    if not value:
        return DEFAULT_PLAN
    if value in _PLAN_ALIASES:
        return _PLAN_ALIASES[value]
    try:
        return PlanCode(value)
    except ValueError:
        return DEFAULT_PLAN


def get_plan_config(plan_code: str | PlanCode | None) -> PlanRuntimeConfig:
    """Return the immutable runtime configuration for a normalized plan."""

    return _PLAN_CONFIGS[normalize_plan_code(plan_code)]


def _normalize_requested_length(
    requested_length: str | DigestLength | None,
) -> DigestLength:
    if isinstance(requested_length, DigestLength):
        return requested_length
    if requested_length is None:
        return DigestLength.SHORT
    try:
        return DigestLength(str(requested_length).strip().lower())
    except ValueError:
        return DigestLength.SHORT


def resolve_digest_policy(
    plan_code: str | PlanCode | None,
    requested_length: str | DigestLength | None,
) -> DigestPolicy:
    """Clamp a requested length to the plan maximum and derive its atom cap.

    Missing or unsupported requested lengths fail safe to ``short`` rather
    than accidentally granting a medium or long digest.
    """

    config = get_plan_config(plan_code)
    requested = _normalize_requested_length(requested_length)
    final_length = min(
        (requested, config.max_digest_length),
        key=_LENGTH_ORDER.__getitem__,
    )
    return DigestPolicy(
        plan_code=config.code,
        requested_length=requested,
        final_length=final_length,
        atom_cap=_ATOM_CAPS[final_length],
    )


def _parse_feature(feature: str | PlanFeature) -> PlanFeature | None:
    if isinstance(feature, PlanFeature):
        return feature
    value = str(feature or "").strip().lower()
    return _FEATURE_ALIASES.get(value)


def plan_allows_feature(
    plan_code: str | PlanCode | None,
    feature: str | PlanFeature,
) -> bool:
    """Return whether the normalized plan allows a known feature.

    Unknown feature values always fail closed.
    """

    parsed_feature = _parse_feature(feature)
    if parsed_feature is None:
        return False
    return parsed_feature in get_plan_config(plan_code).features


_SQL_GET_EFFECTIVE_PLAN = text(
    """
    SELECT plan
    FROM entitlements
    WHERE user_id = :user_id
      AND active = true
      AND started_at <= :now
      AND (expires_at IS NULL OR expires_at > :now)
    ORDER BY started_at DESC, id DESC
    LIMIT 1
    """
)


def _entitlement_now(now: datetime | None) -> datetime:
    """Convert an aware instant to the schema's naive-UTC representation."""

    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return instant.astimezone(timezone.utc).replace(tzinfo=None)


def get_user_plan_code(
    db: Session,
    user_id: int,
    *,
    now: datetime | None = None,
) -> PlanCode:
    """Resolve one user's effective plan at an explicit UTC instant.

    Before Issue #43 enforces one active row, conflicts resolve to the row
    with the latest ``started_at`` and then the highest ``id``.  An unknown
    value in that winning row resolves to ``demo``; policy never falls back to
    an older row that might grant more access.
    """

    row = db.execute(
        _SQL_GET_EFFECTIVE_PLAN,
        {"user_id": user_id, "now": _entitlement_now(now)},
    ).first()
    if row is None:
        return DEFAULT_PLAN
    return normalize_plan_code(row[0])


def get_user_plan_config(
    db: Session,
    user_id: int,
    *,
    now: datetime | None = None,
) -> PlanRuntimeConfig:
    """Return runtime configuration for a user's effective plan."""

    return get_plan_config(get_user_plan_code(db, user_id, now=now))


# ---------------------------------------------------------------------------
# Compatibility API.  These names delegate to the canonical contracts and
# remain only until Issue #42 migrates their callers.
# ---------------------------------------------------------------------------

PlanType: TypeAlias = PlanCode
DigestCap: TypeAlias = DigestLength


def normalise_plan_code(plan_raw: str | PlanCode | None) -> PlanCode:
    """Deprecated British-spelling compatibility wrapper."""

    return normalize_plan_code(plan_raw)


def get_plan_runtime_config(
    code: str | PlanCode | None,
) -> PlanRuntimeConfig:
    """Deprecated compatibility wrapper; use :func:`get_plan_config`."""

    return get_plan_config(code)


def get_user_plan(db: Session, user_id: int, **kwargs: object) -> PlanCode:
    """Deprecated compatibility wrapper returning only :class:`PlanCode`."""

    now = kwargs.get("now")
    if now is not None and not isinstance(now, datetime):
        raise TypeError("now must be a datetime or None")
    return get_user_plan_code(db, user_id, now=now)


def get_plan_runtime_config_for_user(
    db: Session,
    user_id: int,
    **kwargs: object,
) -> PlanRuntimeConfig:
    """Deprecated compatibility wrapper; use :func:`get_user_plan_config`."""

    now = kwargs.get("now")
    if now is not None and not isinstance(now, datetime):
        raise TypeError("now must be a datetime or None")
    return get_user_plan_config(db, user_id, now=now)


def plan_max_digest_length(plan: str | PlanCode | None) -> DigestLength:
    """Deprecated compatibility wrapper for the plan maximum length."""

    return get_plan_config(plan).max_digest_length


def is_feature_allowed_for_plan(
    plan: str | PlanCode | None,
    feature: str | PlanFeature,
) -> bool:
    """Deprecated compatibility wrapper for :func:`plan_allows_feature`."""

    return plan_allows_feature(plan, feature)


def is_feature_allowed_for_user(
    db: Session,
    user_id: int,
    feature: str | PlanFeature,
    **kwargs: object,
) -> bool:
    """Deprecated compatibility wrapper for the canonical user plan check."""

    now = kwargs.get("now")
    if now is not None and not isinstance(now, datetime):
        raise TypeError("now must be a datetime or None")
    return plan_allows_feature(
        get_user_plan_code(db, user_id, now=now),
        feature,
    )


def get_plan_display_name(plan_code: str, locale: str | None = None) -> str:
    """Return the existing lightweight localized display name."""

    code = normalize_plan_code(plan_code)
    base = (locale or "").strip().lower().split("-")[0] or "en"
    if base == "ru":
        return {
            PlanCode.DEMO: "Демо",
            PlanCode.DAILY: "Daily Focus",
            PlanCode.FULL: "Full",
            PlanCode.INTERNAL: "Internal",
        }[code]
    return {
        PlanCode.DEMO: "Demo",
        PlanCode.DAILY: "Daily Focus",
        PlanCode.FULL: "Full",
        PlanCode.INTERNAL: "Internal",
    }[code]


def plan_title_key(plan_code: str | PlanCode) -> str:
    """Return the existing i18n key for a plan name."""

    return f"tg.plan.name.{normalize_plan_code(plan_code).value}"


def feature_title_key(feature: PlanFeature) -> str:
    """Return the existing i18n key for a canonical feature label."""

    if feature == PlanFeature.DAILY_DIGEST:
        return "tg.plan.feature.digest"
    if feature == PlanFeature.STRONG_ALERTS:
        return "tg.plan.feature.alerts"
    if feature == PlanFeature.CALENDAR_ICS:
        return "tg.plan.feature.calendar"
    if feature == PlanFeature.QUIET_MODE:
        return "tg.plan.feature.quiet_mode"
    return "tg.plan.feature.unknown"
