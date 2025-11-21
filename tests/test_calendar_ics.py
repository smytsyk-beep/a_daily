# tests/test_calendar_ics.py
from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import insert

from app.db import SessionLocal
from app import models
from app.calendar_ics import build_calendar_ics_for_user


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _create_user(db) -> models.User:
    u = models.User(
        tg_user_id=f"test_ics_user_{uuid.uuid4().hex}",
        locale="en",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_build_calendar_ics_for_user_contains_events_and_summaries(db_session):
    db = db_session
    user = _create_user(db)

    # контент-атом под наш topic_tag
    db.execute(
        insert(models.ContentAtom).values(
            locale="en",
            topic_tag="ics_test_event",
            style="neutral",
            body="ICS Test Event (EN)",
        )
    )

    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    ts1 = now_utc + timedelta(hours=1)
    ts2 = now_utc + timedelta(days=1, hours=2)

    # два транзита в ближайшие дни
    db.execute(
        insert(models.TransitEvent),
        [
            {
                "user_id": user.id,
                "ts_utc": ts1.replace(tzinfo=None),  # в БД храним naive как UTC
                "kind": "generic",
                "payload": {
                    "module": "astro_core",
                    "topic_tag": "ics_test_event",
                    "strength": 0.8,
                },
            },
            {
                "user_id": user.id,
                "ts_utc": ts2.replace(tzinfo=None),
                "kind": "generic",
                "payload": {
                    "module": "astro_core",
                    "topic_tag": "ics_test_event",
                    "strength": 0.9,
                },
            },
        ],
    )
    db.commit()

    ics = build_calendar_ics_for_user(
        db,
        user_id=user.id,
        days_ahead=3,
        tz_override="Europe/Berlin",
    )

    assert "BEGIN:VCALENDAR" in ics
    assert "END:VCALENDAR" in ics
    # два события
    assert ics.count("BEGIN:VEVENT") == 2
    # текст из ContentAtom
    assert "SUMMARY:ICS Test Event (EN)" in ics
    # таймзона прокинута в заголовок
    assert "X-WR-TIMEZONE:Europe/Berlin" in ics
