# src/app/routes_modules.py

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query, Response, HTTPException

from app.deps import SessionDep
from app.models import Event, User, Entitlement
from app.repo import list_enabled_modules, session_scope
from app.schemas import DigestDayOut, EventOut, StrongAlertsOut
from app.calendar_ics import build_calendar_ics_for_user_ref
from common.plans import PlanFeature, is_feature_allowed_for_user

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
    (numeric id или tg_user_id) с учётом планов.

    Важно:
    - Если у пользователя НЕТ ни одного активного entitlement — ведём себя как раньше,
      без гейтинга (для старых/тестовых пользователей).
    - Если есть entitlements — проверяем, разрешена ли фича CALENDAR_ICS.
      Если нет — 403.
    """

    # --- Разрешаем/запрещаем календарь по плану, но только для пользователей с entitlements ---
    with session_scope() as db:
        # resolve user: numeric id или tg_user_id
        if user_ref.isdigit():
            user = db.get(User, int(user_ref))
        else:
            user = db.query(User).filter(User.tg_user_id == str(user_ref)).first()

        # Если пользователя не нашли — пусть разрулит сам build_calendar_ics_for_user_ref
        # (он, скорее всего, бросит ValueError, ниже мы это переведём в 404).
        if user:
            has_entitlement = (
                db.query(Entitlement)
                .filter(
                    Entitlement.user_id == user.id,
                    Entitlement.active.is_(True),
                )
                .first()
                is not None
            )

            if has_entitlement:
                # Для юзеров с entitlements — строгий гейтинг по фиче CALENDAR_ICS.
                if not is_feature_allowed_for_user(
                    db,
                    user.id,
                    PlanFeature.CALENDAR_ICS,
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Calendar feature is not available for this plan.",
                    )

    # --- Если по плану всё ок — строим .ics как раньше ---
    try:
        body = build_calendar_ics_for_user_ref(
            user_ref=user_ref,
            days_ahead=days,
            tz=tz,
        )
    except ValueError as e:
        # типичный кейс — пользователь не найден / нет данных
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
