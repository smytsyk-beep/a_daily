from datetime import date, datetime
from fastapi import APIRouter, Query, Response

from app.deps import SessionDep  # тип сессии из твоего deps
from app.models import Event
from app.repo import list_enabled_modules
from app.schemas import DigestDayOut, EventOut, StrongAlertsOut

# Роутер с твоим префиксом
router = APIRouter(prefix="/modules", tags=["modules"])
# Доп. роутер без префикса — чтобы пройти контракты/тесты
public = APIRouter(prefix="", tags=["modules-public"])

# -------- общие хелперы (чтобы не дублировать код) --------


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


def _calendar_ics_core() -> Response:
    body = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//AstroDaily//EN\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:demo-1@astrodaily\r\n"
        "DTSTAMP:20250101T000000Z\r\n"
        "DTSTART:20250101T000000Z\r\n"
        "DTEND:20250101T010000Z\r\n"
        "SUMMARY:AstroDaily Placeholder\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return Response(content=body, media_type="text/calendar; charset=utf-8")


def _modules_list_core(db: SessionDep):
    rows = list_enabled_modules(db)
    return [
        {"module": r.module, "enabled": r.enabled, "config": r.config} for r in rows
    ]


# -------- /modules/* маршруты (как у тебя было) --------


@router.get("/digest/daily", response_model=DigestDayOut)
def daily_digest(d: date = Query(default_factory=date.today), db: SessionDep = None):
    return _daily_digest_core(d, db)


@router.get("/alerts/strong", response_model=StrongAlertsOut)
def strong_alerts(db: SessionDep = None):
    return _strong_alerts_core(db)


@router.get("/calendar.ics")
def calendar_ics(_: SessionDep = None):
    return _calendar_ics_core()


@router.get(
    "/"
)  # явный слэш — чтобы не было ошибки "Prefix and path cannot be both empty"
def modules_list(db: SessionDep = None):
    return _modules_list_core(db)


# -------- дубли без префикса для контрактов/тестов --------


@public.get("/digest/daily", response_model=DigestDayOut)
def daily_digest_public(
    d: date = Query(default_factory=date.today), db: SessionDep = None
):
    return _daily_digest_core(d, db)


@public.get("/alerts/strong", response_model=StrongAlertsOut)
def strong_alerts_public(db: SessionDep = None):
    return _strong_alerts_core(db)


@public.get("/calendar.ics")
def calendar_ics_public(_: SessionDep = None):
    return _calendar_ics_core()


@public.get("/")
def modules_list_public(db: SessionDep = None):
    return _modules_list_core(db)
