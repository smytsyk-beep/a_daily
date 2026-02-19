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


def _llm_metrics(db) -> dict:
    """Метрики из llm_usage_log для мониторинга затрат и cache hit rate."""
    try:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        q_today = (
            db.query(
                sa.func.count(models.LLMUsageLog.id).label("requests"),
                sa.func.coalesce(
                    sa.func.sum(models.LLMUsageLog.estimated_cost_usd), 0
                ).label("cost_usd"),
                sa.func.sum(
                    sa.case((models.LLMUsageLog.cache_hit.is_(True), 1), else_=0)
                ).label("cache_hits"),
            ).filter(models.LLMUsageLog.created_at >= today_start)
        ).one()
        q_all = (
            db.query(
                sa.func.count(models.LLMUsageLog.id).label("requests"),
                sa.func.coalesce(
                    sa.func.sum(models.LLMUsageLog.estimated_cost_usd), 0
                ).label("cost_usd"),
                sa.func.sum(
                    sa.case((models.LLMUsageLog.cache_hit.is_(True), 1), else_=0)
                ).label("cache_hits"),
            )
        ).one()
        requests_today = q_today.requests or 0
        cost_today = float(q_today.cost_usd or 0)
        requests_total = q_all.requests or 0
        cost_total = float(q_all.cost_usd or 0)
        cache_hits_total = (q_all.cache_hits or 0) or 0
        cache_hit_rate = (cache_hits_total / requests_total) if requests_total else 0.0
        return {
            "requests_today": requests_today,
            "cost_today_usd": round(cost_today, 6),
            "requests_total": requests_total,
            "cost_total_usd": round(cost_total, 6),
            "cache_hit_rate": round(cache_hit_rate, 4),
        }
    except Exception:
        return {
            "requests_today": 0,
            "cost_today_usd": 0.0,
            "requests_total": 0,
            "cost_total_usd": 0.0,
            "cache_hit_rate": 0.0,
            "error": "llm_usage_log unavailable",
        }


@router.get("/metrics")
def get_metrics() -> dict:
    """
    Простой JSON-эндпоинт с базовыми метриками приложения и БД.

    Включает LLM-метрики (запросы/день, затраты, cache hit rate) для мониторинга.
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

        # Активные энтайтлменты по планам
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

        llm = _llm_metrics(db)

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
        "llm": llm,
    }
