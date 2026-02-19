# src/app/services/transit_events_precompute.py
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, List
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import models
from app.astro.transit_service import (
    compute_daily_digest_transits,
    compute_strong_alert_transits,
    _local_noon_to_utc,  # мы ее уже сделали в transit_service.py
)


def _daterange(start: date, end: date) -> Iterable[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _user_local_today(user: models.User) -> date:
    tzid = user.timezone or "UTC"
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tzid)).date()


def _event_title(e: dict) -> str:
    # пример: "Transit: mars square sun"
    return f"Transit: {e['transit_body']} {e['aspect']} {e['natal_body']}"


def precompute_transit_events_for_user(
    db: Session,
    *,
    user_id: int,
    start_local: date,
    end_local: date,
) -> int:
    user = db.query(models.User).filter(models.User.id == user_id).one()

    # если нет birth_data — пропускаем
    birth = (
        db.query(models.BirthData).filter(models.BirthData.user_id == user_id).first()
    )
    if birth is None:
        return 0

    tzid = user.timezone or "UTC"

    # для чистого upsert-подхода: удаляем только транзитные события в диапазоне
    start_ts_utc = _local_noon_to_utc(start_local, tzid)
    end_ts_utc = _local_noon_to_utc(end_local, tzid)

    db.query(models.Event).filter(
        models.Event.user_id == user_id,
        models.Event.kind == "transit_aspect",
        models.Event.ts >= start_ts_utc,
        models.Event.ts <= end_ts_utc,
    ).delete(synchronize_session=False)

    created = 0

    for day_local in _daterange(start_local, end_local):
        ts_utc = _local_noon_to_utc(day_local, tzid)

        digest_aspects = compute_daily_digest_transits(
            db, user_id=user_id, local_date=day_local
        )
        strong_aspects = compute_strong_alert_transits(
            db, user_id=user_id, local_date=day_local
        )

        # сохраняем каждое событие отдельной строкой Event
        for bucket, aspects in (("digest", digest_aspects), ("strong", strong_aspects)):
            for a in aspects:
                payload = asdict(a)
                payload["bucket"] = bucket
                payload["local_date"] = day_local.isoformat()
                payload["tzid"] = tzid

                db.add(
                    models.Event(
                        user_id=user_id,
                        kind="transit_aspect",
                        ts=ts_utc,
                        title=_event_title(payload),
                        details=payload,
                    )
                )
                created += 1

    db.commit()
    return created


def precompute_transit_events_for_all_users(
    db: Session,
    *,
    days_back: int = 7,
    days_forward: int = 30,
) -> int:
    total = 0

    user_ids = [u.id for u in db.query(models.User.id).all()]
    for uid in user_ids:
        user = db.query(models.User).filter(models.User.id == uid).one()
        today_local = _user_local_today(user)
        start_local = today_local - timedelta(days=days_back)
        end_local = today_local + timedelta(days=days_forward)

        total += precompute_transit_events_for_user(
            db, user_id=uid, start_local=start_local, end_local=end_local
        )

    return total


def get_active_user_ids_for_precompute(db: Session) -> List[int]:
    """
    Пользователи, для которых имеет смысл precompute транзитов:
    есть birth_data (иначе транзиты не посчитать).
    """
    from sqlalchemy import select

    rows = db.execute(
        select(models.BirthData.user_id).distinct()
    ).fetchall()
    return [r[0] for r in rows]


def precompute_transit_events_tomorrow_for_active_users(db: Session) -> int:
    """
    Pre-compute транзитов на завтра (в локальной дате пользователя) для всех
    активных пользователей (с birth_data). Вызывать из cron/worker, например в 3:00 UTC.
    """
    import logging

    logger = logging.getLogger(__name__)

    user_ids = get_active_user_ids_for_precompute(db)
    if not user_ids:
        logger.info("[PRECOMPUTE] No active users with birth_data, skip")
        return 0

    total = 0
    for uid in user_ids:
        try:
            user = db.query(models.User).filter(models.User.id == uid).one()
            today_local = _user_local_today(user)
            tomorrow_local = today_local + timedelta(days=1)
            n = precompute_transit_events_for_user(
                db,
                user_id=uid,
                start_local=tomorrow_local,
                end_local=tomorrow_local,
            )
            total += n
        except Exception as e:
            logger.warning(
                "[PRECOMPUTE] Failed for user_id=%s: %s",
                uid,
                e,
                exc_info=True,
            )
            # сессия может быть в плохом состоянии — для следующего user нужна новая?
            # precompute_transit_events_for_user делает commit(), при ошибке — rollback не здесь
            db.rollback()

    logger.info(
        "[PRECOMPUTE] Tomorrow: %d users, %d events written",
        len(user_ids),
        total,
    )
    return total
