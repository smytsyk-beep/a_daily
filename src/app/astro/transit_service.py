# src/app/astro/transit_service.py
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import List
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import models
from app.astro.natal import get_or_compute_natal
from app.astro.skyfield_client import compute_all_bodies
from app.astro.transits import TransitAspectEvent, detect_transit_aspects


ORB_DIGEST = 2.0
ORB_STRONG_ALERTS = 1.0


def _local_noon_to_utc(dt_local_date: date, tzid: str) -> datetime:
    tz = ZoneInfo(tzid)
    local_dt = datetime.combine(dt_local_date, time(12, 0)).replace(tzinfo=tz)
    return local_dt.astimezone(timezone.utc)


def compute_transit_aspects_for_local_date(
    db: Session,
    *,
    user_id: int,
    local_date: date,
    orb_deg: float,
    include_moon: bool = True,
) -> List[TransitAspectEvent]:
    """
    Вычисляет транзитные аспекты для пользователя на указанную локальную дату.

    1. Получаем натальную карту (с кэшированием)
    2. Вычисляем позиции транзитных планет на полдень локальной даты
    3. Находим аспекты между транзитными и натальными планетами
    """
    import logging

    logger = logging.getLogger(__name__)

    user = db.query(models.User).filter(models.User.id == user_id).one()
    tzid = user.timezone or "UTC"

    logger.info(
        "[TRANSIT] Computing aspects for user_id=%s local_date=%s tzid=%s orb=%.1f",
        user_id,
        local_date,
        tzid,
        orb_deg,
    )

    # BirthData берём по user_id (если у тебя связь другая — скажи, поправлю)
    birth = db.query(models.BirthData).filter(models.BirthData.user_id == user_id).one()

    natal = get_or_compute_natal(db, birth)
    natal_lon = {name: pos.lon for name, pos in natal.bodies.items()}

    logger.info(
        "[TRANSIT] Got natal chart with %d bodies for user_id=%s",
        len(natal_lon),
        user_id,
    )

    dt_utc = _local_noon_to_utc(local_date, tzid)

    transit_bodies = compute_all_bodies(dt_utc=dt_utc)  # геоцентрически
    transit_lon = {name: pos.lon for name, pos in transit_bodies.items()}

    logger.info(
        "[TRANSIT] Computed transit positions for %d bodies at %s UTC",
        len(transit_bodies),
        dt_utc.isoformat(),
    )

    if not include_moon:
        transit_lon.pop("moon", None)

    aspects = detect_transit_aspects(transit_lon, natal_lon, orb_deg=orb_deg)

    logger.info(
        "[TRANSIT] Found %d transit aspects for user_id=%s local_date=%s",
        len(aspects),
        user_id,
        local_date,
    )

    return aspects


def compute_daily_digest_transits(db: Session, *, user_id: int, local_date: date):
    return compute_transit_aspects_for_local_date(
        db,
        user_id=user_id,
        local_date=local_date,
        orb_deg=ORB_DIGEST,
        include_moon=True,
    )


def compute_strong_alert_transits(db: Session, *, user_id: int, local_date: date):
    # для алертов обычно лучше без Луны (меньше “шума”)
    return compute_transit_aspects_for_local_date(
        db,
        user_id=user_id,
        local_date=local_date,
        orb_deg=ORB_STRONG_ALERTS,
        include_moon=False,
    )
