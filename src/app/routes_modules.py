from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query, Response, HTTPException

from app.deps import SessionDep
from app.models import Event
from app.repo import list_enabled_modules
from app.schemas import DigestDayOut, EventOut, StrongAlertsOut
from app.calendar_ics import build_calendar_ics_for_user_ref

# Роутер с префиксом /modules
router = APIRouter(prefix="/modules", tags=["modules"])
# Публичный роутер без префикса — для контрактов/тестов
public = APIRouter(prefix="", tags=["modules-public"])


# ---------- общие хелперы ----------


def _daily_digest_core(d: date, db: SessionDep) -> DigestDayOut:
    rows = (
        db.query(Event)
        .filter(Event.kind.in_(["transit", "strong"]))
        .order_by(Event.ts.asc())
        .limit(50)
        .all()
    )
    return DigestDayOut(
        date=d.isoformat(),
        events=[EventOut.model_validate(r.__dict__) for r in rows],
    )


def _strong_alerts_core(db: SessionDep) -> StrongAlertsOut:
    rows = (
        db.query(Event)
        .filter(Event.kind == "strong")
        .order_by(Event.ts.desc())
        .limit(50)
        .all()
    )
    return StrongAlertsOut(
        ts=datetime.utcnow(),
        count=len(rows),
        events=[EventOut.model_validate(r.__dict__) for r in rows],
    )


def _calendar_ics_core(
    user_ref: str,
    days: int,
    tz: Optional[str],
) -> Response:
    """
    Обёртка над build_calendar_ics_for_user_ref: строим .ics для user_ref
    (numeric id или tg_user_id).
    """
    try:
        body = build_calendar_ics_for_user_ref(
            user_ref=user_ref,
            days_ahead=days,
            tz=tz,
        )
    except ValueError as e:
        # напр., если пользователь не найден
        raise HTTPException(status_code=404, detail=str(e))

    return Response(content=body, media_type="text/calendar; charset=utf-8")


def _modules_list_core(db: SessionDep):
    rows = list_enabled_modules(db)
    return [
        {"module": r.module, "enabled": r.enabled, "config": r.config} for r in rows
    ]


# ---------- /modules/* маршруты ----------


@router.get("/digest/daily", response_model=DigestDayOut)
def daily_digest(
    d: date = Query(default_factory=date.today),
    db: SessionDep = None,
) -> DigestDayOut:
    return _daily_digest_core(d, db)


@router.get("/alerts/strong", response_model=StrongAlertsOut)
def strong_alerts(db: SessionDep = None) -> StrongAlertsOut:
    return _strong_alerts_core(db)


@router.get("/calendar.ics")
def calendar_ics(
    user_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="numeric id или tg_user_id",
    ),
    days: int = Query(
        7,
        ge=1,
        le=90,
        description="Горизонт выгрузки в днях (1..90)",
    ),
    tz: Optional[str] = Query(
        None,
        min_length=3,
        max_length=64,
        description="IANA timezone, e.g. 'Europe/Berlin' (override user.timezone)",
    ),
    _: SessionDep = None,
) -> Response:
    return _calendar_ics_core(user_ref=user_id, days=days, tz=tz)


@router.get("/")  # явный слэш, чтобы не было пустого пути
def modules_list(db: SessionDep = None):
    return _modules_list_core(db)


# ---------- публичные дубли без префикса ----------


@public.get("/digest/daily", response_model=DigestDayOut)
def daily_digest_public(
    d: date = Query(default_factory=date.today),
    db: SessionDep = None,
) -> DigestDayOut:
    return _daily_digest_core(d, db)


@public.get("/alerts/strong", response_model=StrongAlertsOut)
def strong_alerts_public(db: SessionDep = None) -> StrongAlertsOut:
    return _strong_alerts_core(db)


@public.get("/calendar.ics")
def calendar_ics_public(
    user_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="numeric id или tg_user_id",
    ),
    days: int = Query(
        7,
        ge=1,
        le=90,
        description="Горизонт выгрузки в днях (1..90)",
    ),
    tz: Optional[str] = Query(
        None,
        min_length=3,
        max_length=64,
        description="IANA timezone, e.g. 'Europe/Berlin' (override user.timezone)",
    ),
    _: SessionDep = None,
) -> Response:
    return _calendar_ics_core(user_ref=user_id, days=days, tz=tz)


@public.get("/")
def modules_list_public(db: SessionDep = None):
    return _modules_list_core(db)
