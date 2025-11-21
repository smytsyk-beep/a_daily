from __future__ import annotations

from datetime import datetime, date, time, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import TransitEvent
from app.repo import resolve_user_id


def _day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """Возвращает (start_utc, end_utc) для суток в UTC."""
    start = datetime.combine(day, time(0, 0), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def get_daily_transits(
    db: Session,
    user_id: int,
    day: Optional[date] = None,
) -> List[TransitEvent]:
    """
    Возвращает все транзитные события пользователя за указанный день (UTC).
    Ничего не создаёт, просто читает из таблицы transit_events.
    """
    if day is None:
        day = datetime.utcnow().date()

    start, end = _day_bounds_utc(day)

    return (
        db.query(TransitEvent)
        .filter(
            TransitEvent.user_id == user_id,
            TransitEvent.ts_utc >= start,
            TransitEvent.ts_utc < end,
        )
        .order_by(TransitEvent.ts_utc)
        .all()
    )


def ensure_daily_transits(
    db: Session,
    user_ref,
    day: Optional[date] = None,
) -> List[TransitEvent]:
    """
    Высокоуровневый helper:
      * преобразует user_ref -> user_id через resolve_user_id
      * читает транзиты за день
      * если их нет — создаёт один «generic» транзит посреди дня.

    Это временный stub-астрокор для MVP, пока не подключена реальная библиотека.
    """
    if day is None:
        day = datetime.utcnow().date()

    user_id = resolve_user_id(db, user_ref)
    events = get_daily_transits(db, user_id=user_id, day=day)
    if events:
        return events

    start, end = _day_bounds_utc(day)
    mid_ts = start + (end - start) / 2

    payload = {
        "module": "astro_core",
        "kind": "generic_day",
        "topic_tag": "generic_day_overview",
        "strength": 0.5,
    }
    ev = TransitEvent(
        user_id=user_id,
        ts_utc=mid_ts,
        kind="generic",
        payload=payload,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return [ev]
