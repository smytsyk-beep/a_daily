# src/common/entitlements.py

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from common.plans import PlanCode, normalise_plan_code


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


def get_active_plan_code(
    db: Session, user_id: int, now: datetime | None = None
) -> PlanCode:
    """
    Возвращает активный plan_code для пользователя.

    Если записи нет — DEFAULT_PLAN ("daily").
    Также нормализует legacy plan values: basic/pro -> daily/full.
    """
    now_dt = now or datetime.utcnow()
    row = db.execute(_SQL_GET_ACTIVE_PLAN, {"user_id": user_id, "now": now_dt}).first()
    if not row:
        return normalise_plan_code(None)
    return normalise_plan_code(str(row[0]))
