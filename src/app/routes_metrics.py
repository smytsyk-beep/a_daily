# src/app/routes_metrics.py

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
import sqlalchemy as sa

from app import models
from app.repo import session_scope
from common.config import settings

router = APIRouter(tags=["metrics"])

# Зафиксируем время старта процесса, чтобы считать uptime
STARTED_AT = datetime.now(timezone.utc)


@router.get("/metrics")
def get_metrics() -> dict:
    """
    Простой JSON-эндпоинт с базовыми метриками приложения и БД.

    Это не Prometheus-формат, а human/JSON-friendly сводка.
    """
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - STARTED_AT).total_seconds())

    with session_scope() as db:
        # Базовые счётчики, которые у нас точно есть
        users_count = db.query(models.User).count()
        content_atoms_count = db.query(models.ContentAtom).count()

        # Дополнительные счётчики по событиям
        events_count = db.query(models.Event).count()
        feedback_count = db.query(models.EventFeedback).count()

        # Активные энтайтлменты по планам:
        # простая группировка по полю plan для включённых записей
        entitlements_q = (
            db.query(
                models.Entitlement.plan.label("plan"),
                sa.func.count(models.Entitlement.id).label("cnt"),
            )
            .filter(models.Entitlement.active.is_(True))
            .group_by(models.Entitlement.plan)
        )
        entitlements_by_plan = {row.plan: row.cnt for row in entitlements_q.all()}
        entitlements_total = sum(entitlements_by_plan.values())

    return {
        "app": {
            "name": getattr(settings, "APP_NAME", "astrodaily"),
            "env": getattr(settings, "APP_ENV", "dev"),
            "version": getattr(settings, "APP_VERSION", None),
            "uptime_seconds": uptime_seconds,
        },
        "db": {
            "users": users_count,
            "content_atoms": content_atoms_count,
            "events": events_count,
            "feedback": feedback_count,
            "entitlements": {
                "total_active": entitlements_total,
                "by_plan": entitlements_by_plan,
            },
        },
    }
