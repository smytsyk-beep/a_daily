# tests/test_astro_core.py
from datetime import date, datetime, timezone
import uuid

import pytest
from sqlalchemy import insert

from app.db import SessionLocal
from app import models
from app.astro_core import get_daily_transits, ensure_daily_transits


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
        tg_user_id=f"test_user_core_{uuid.uuid4().hex}",
        locale="en",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_get_daily_transits_returns_existing_events(db_session):
    db = db_session
    user = _create_user(db)
    day = date(2025, 1, 1)

    ts = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    db.execute(
        insert(models.TransitEvent).values(
            user_id=user.id,
            ts_utc=ts,
            kind="generic",
            payload={"module": "astro_core", "topic_tag": "test_tag", "strength": 0.9},
        )
    )
    db.commit()

    events = get_daily_transits(db, user_id=user.id, day=day)
    assert len(events) == 1
    assert events[0].user_id == user.id
    assert events[0].payload["topic_tag"] == "test_tag"


def test_ensure_daily_transits_creates_generic_if_empty(db_session):
    db = db_session
    user = _create_user(db)
    day = date(2025, 1, 2)

    events = ensure_daily_transits(db, user_ref=user.id, day=day)

    assert len(events) == 1
    ev = events[0]
    assert ev.user_id == user.id
    assert ev.kind == "generic"
