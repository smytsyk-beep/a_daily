"""Deprecated entitlement compatibility API.

The canonical time-aware entitlement reader lives in :mod:`common.plans`.
This module remains only for existing callers until Issue #42.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from common.plans import PlanCode, get_user_plan_code


def get_active_plan_code(
    db: Session,
    user_id: int,
    now: datetime | None = None,
) -> PlanCode:
    """Deprecated wrapper for :func:`common.plans.get_user_plan_code`."""

    return get_user_plan_code(db, user_id, now=now)
