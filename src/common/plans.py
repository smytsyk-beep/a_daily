# src/common/plans.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, FrozenSet, Literal, Optional, Set, Union

from sqlalchemy import text
from sqlalchemy.orm import Session

# =========================
# Plan codes (single source of truth)
# =========================

PlanCode = Literal["demo", "daily", "full", "internal"]

# Default plan if entitlements отсутствуют (до Stripe): daily/free
DEFAULT_PLAN: PlanCode = "daily"
DEFAULT_PLAN_CODE: PlanCode = DEFAULT_PLAN  # backward-compat alias

# Legacy values that may exist in entitlements.plan (your DB screenshot shows: basic/pro)
_PLAN_ALIASES: dict[str, PlanCode] = {
    "basic": "daily",
    "pro": "full",
    # safety aliases
    "free": "daily",
    "premium": "full",
}

# =========================
# Features (gating)
# =========================


class PlanFeature(str, Enum):
    DAILY_DIGEST = "daily_digest"  # /today
    STRONG_ALERTS = "strong_alerts"  # strong_events_alerts
    CALENDAR_ICS = "calendar_ics"  # /calendar.ics
    QUIET_MODE = "quiet_mode"  # /snooze etc (delivery controls)

    # alias for old name used earlier in code/tests
    ALERTS_STRONG = "strong_alerts"


DigestCap = Literal["short", "medium", "long"]


@dataclass(frozen=True)
class PlanRuntimeConfig:
    code: PlanCode
    digest_cap: DigestCap
    features: FrozenSet[PlanFeature]


_PLAN_CONFIGS: Dict[PlanCode, PlanRuntimeConfig] = {
    "demo": PlanRuntimeConfig(
        code="demo",
        digest_cap="short",
        features=frozenset({PlanFeature.DAILY_DIGEST}),
    ),
    "daily": PlanRuntimeConfig(
        code="daily",
        digest_cap="medium",
        features=frozenset({PlanFeature.DAILY_DIGEST, PlanFeature.QUIET_MODE}),
    ),
    "full": PlanRuntimeConfig(
        code="full",
        digest_cap="long",
        features=frozenset(
            {
                PlanFeature.DAILY_DIGEST,
                PlanFeature.QUIET_MODE,
                PlanFeature.STRONG_ALERTS,
                PlanFeature.CALENDAR_ICS,
            }
        ),
    ),
    "internal": PlanRuntimeConfig(
        code="internal",
        digest_cap="long",
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


def all_plan_codes() -> Set[PlanCode]:
    return set(_PLAN_CONFIGS.keys())


# Backwards-compat alias (старый код воспринимал plan как просто строку)
PlanType = PlanCode


def get_plan_config(code: Optional[PlanCode]) -> PlanRuntimeConfig:
    if code is None:
        code = DEFAULT_PLAN
    cfg = _PLAN_CONFIGS.get(code)
    if cfg is None:
        cfg = _PLAN_CONFIGS[DEFAULT_PLAN]
    return cfg


def get_plan_runtime_config(code: Optional[PlanCode]) -> PlanRuntimeConfig:
    # backward-compat function name
    return get_plan_config(code)


def normalise_plan_code(plan_raw: str | None) -> PlanType:
    if not plan_raw:
        return DEFAULT_PLAN

    raw = plan_raw.strip().lower()
    raw = _PLAN_ALIASES.get(raw, raw)

    if raw not in _PLAN_CONFIGS:
        return DEFAULT_PLAN

    return raw  # type: ignore[return-value]


def plan_allows_feature(plan: PlanType, feature: PlanFeature) -> bool:
    cfg = get_plan_config(plan)  # type: ignore[arg-type]
    return feature in cfg.features


def plan_max_digest_length(plan: PlanType) -> str:
    cfg = get_plan_config(plan)  # type: ignore[arg-type]
    return cfg.digest_cap


# =========================
# Entitlements -> current plan (DB)
# =========================

_SQL_GET_ACTIVE_PLAN = text(
    """
    SELECT plan
    FROM entitlements
    WHERE user_id = :user_id
      AND active = true
      AND started_at <= :now
      AND (expires_at IS NULL OR expires_at > :now)
    ORDER BY started_at DESC
    LIMIT 1
    """
)


def get_user_plan(db: Session, user_id: int, **kwargs) -> PlanCode:
    """
    SINGLE entrypoint used across app/tests.

    Reads current plan from entitlements.
    If no active entitlement -> DEFAULT_PLAN ("daily").

    kwargs accepted for backward compatibility (e.g. today=..., now=...).
    """
    now: datetime | None = kwargs.get("now")
    now_dt = now or datetime.utcnow()

    row = db.execute(_SQL_GET_ACTIVE_PLAN, {"user_id": user_id, "now": now_dt}).first()
    if not row:
        return DEFAULT_PLAN

    return normalise_plan_code(str(row[0]))


def get_plan_runtime_config_for_user(
    db: Session, user_id: int, **kwargs
) -> PlanRuntimeConfig:
    code = get_user_plan(db, user_id, **kwargs)
    return get_plan_runtime_config(code)


# =========================
# Backward-compat helpers (replacing old app.plans API)
# =========================


def _parse_feature(feature: Union[str, PlanFeature]) -> PlanFeature | None:
    if isinstance(feature, PlanFeature):
        return feature

    f = (feature or "").strip().lower()
    if f in ("daily_digest", "digest_daily", "digest_daily_demo"):
        return PlanFeature.DAILY_DIGEST
    if f in ("strong_alerts", "alerts_strong"):
        return PlanFeature.STRONG_ALERTS
    if f in ("calendar_ics",):
        return PlanFeature.CALENDAR_ICS
    if f in ("quiet_mode",):
        return PlanFeature.QUIET_MODE

    return None


def is_feature_allowed_for_plan(plan: str, feature: Union[str, PlanFeature]) -> bool:
    code = normalise_plan_code(plan)
    pf = _parse_feature(feature)
    if pf is None:
        return False
    return plan_allows_feature(code, pf)


def is_feature_allowed_for_user(
    db: Session, user_id: int, feature: Union[str, PlanFeature], **kwargs
) -> bool:
    code = get_user_plan(db, user_id, **kwargs)
    pf = _parse_feature(feature)
    if pf is None:
        return False
    return plan_allows_feature(code, pf)


def get_plan_display_name(plan_code: str, locale: str | None = None) -> str:
    """
    Lightweight display name. (User-facing i18n can override via locales later.)

    locale is optional and используется только для базовых RU/ES вариантов.
    """
    code = normalise_plan_code(plan_code)

    loc = (locale or "").strip().lower()
    base = loc.split("-")[0] if loc else "en"

    # brand names: keep "Daily Focus" as a product name; translate Demo only
    if base == "ru":
        return {
            "demo": "Демо",
            "daily": "Daily Focus",
            "full": "Full",
            "internal": "Internal",
        }[code]
    if base == "es":
        return {
            "demo": "Demo",
            "daily": "Daily Focus",
            "full": "Full",
            "internal": "Internal",
        }[code]

    return {
        "demo": "Demo",
        "daily": "Daily Focus",
        "full": "Full",
        "internal": "Internal",
    }[code]


# ---- i18n helper keys (used by Telegram / UI) ----


def plan_title_key(plan_code: str | PlanCode) -> str:
    """
    i18n key for plan name: tg.plan.name.daily / tg.plan.name.full / etc.
    """
    code = normalise_plan_code(str(plan_code))
    return f"tg.plan.name.{code}"


def feature_title_key(feature: PlanFeature) -> str:
    """
    i18n key for feature label.
    """
    if feature == PlanFeature.DAILY_DIGEST:
        return "tg.plan.feature.digest"
    if feature in (PlanFeature.STRONG_ALERTS, PlanFeature.ALERTS_STRONG):
        return "tg.plan.feature.alerts"
    if feature == PlanFeature.CALENDAR_ICS:
        return "tg.plan.feature.calendar"
    if feature == PlanFeature.QUIET_MODE:
        return "tg.plan.feature.quiet_mode"
    return "tg.plan.feature.unknown"
