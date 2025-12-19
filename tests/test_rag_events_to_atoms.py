from datetime import date, datetime, timezone
import uuid

from app.db import SessionLocal
from app import models
from app.content_atoms_rag import select_atoms_for_day, UserProfile


def _create_user(db) -> models.User:
    u = models.User(
        tg_user_id=str(uuid.uuid4()),
        locale="en",
        timezone="Europe/Kyiv",
        delivery_enabled=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_birth_data(db, user_id: int) -> None:
    db.add(
        models.BirthData(
            user_id=user_id,
            birth_date=date(1990, 1, 1),
            birth_time="12:00",
            tz="Europe/Kyiv",
            place="Kyiv",
            lat=50.45,
            lon=30.523,
        )
    )
    db.commit()


def test_select_atoms_uses_events_transit_triggers():
    db = SessionLocal()
    try:
        user = _create_user(db)
        _create_birth_data(db, user_id=user.id)

        unique_trigger = f"test_{uuid.uuid4().hex}_mars_square_sun"

        # атом под конкретный trigger
        atom = models.ContentAtom(
            locale="en",
            topic_tag="general",
            style="neutral",
            body="Mars square Sun test atom",
            trigger=unique_trigger,
            persona_tags=["general"],
        )
        db.add(atom)
        db.commit()
        db.refresh(atom)

        day = date(2025, 1, 15)
        ev = models.Event(
            user_id=user.id,
            kind="transit_aspect",
            ts=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            title="Transit: mars square sun",
            details={
                "bucket": "digest",
                "local_date": day.isoformat(),
                "tzid": "Europe/Kyiv",
                "trigger": unique_trigger,
                "transit_body": "mars",
                "aspect": "square",
                "natal_body": "sun",
                "orb_deg": 0.5,
            },
        )
        db.add(ev)
        db.commit()

        profile = UserProfile(
            locale="en", interests=["general"], preferred_length="medium"
        )
        selected = select_atoms_for_day(
            db=db, user_id=user.id, day=day, user_profile=profile
        )

        assert selected, "expected at least 1 selected atom"
        assert selected[0].atom.id == atom.id
    finally:
        db.close()
