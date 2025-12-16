# tests/test_daily_digest_service.py
from datetime import date

from app.db import SessionLocal
from app import models
from app.daily_digest_service import build_daily_digest_for_user
from app.content_atoms_rag import UserProfile


def _make_user(db) -> models.User:
    user = db.query(models.User).filter(models.User.tg_user_id == "digest_user").first()
    if user:
        return user

    user = models.User(tg_user_id="digest_user", locale="en")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_birth_data(db, user_id: int):
    """
    Для транзитов нужна birth_data с координатами.
    Используем простой stub, как в других тестах.
    """
    existing = (
        db.query(models.BirthData).filter(models.BirthData.user_id == user_id).first()
    )
    if existing:
        return

    bd = models.BirthData(
        user_id=user_id,
        birth_date=date(1990, 1, 1),
        birth_time="12:00",
        tz="UTC",
        lat=10.0,
        lon=20.0,
        place="Test City",
    )
    db.add(bd)
    db.commit()


def _seed_content_atoms(db):
    """
    Создаём один базовый атом, если ещё ни одного нет.
    Важно заполнить NOT NULL поля (body, locale и т.п.).
    """
    existing = (
        db.query(models.ContentAtom)
        .filter(models.ContentAtom.trigger == "generic")
        .first()
    )
    if existing:
        return

    long_text = "This is a longer generic daily guidance text for the digest."

    atom = models.ContentAtom(
        locale="en",
        body=long_text,
        topic_tag="generic_day",
        style="neutral",
        trigger="generic",
        house_tags=["I"],
        persona_tags=["general"],
        strength_hint="light_to_medium",
        copy_short="Short generic guidance.",
        copy_long=long_text,
        cta="Pause, breathe, and set a gentle intention.",
    )
    db.add(atom)
    db.commit()


def test_build_daily_digest_for_user_basic_flow():
    db = SessionLocal()
    try:
        user = _make_user(db)
        _ensure_birth_data(db, user.id)
        _seed_content_atoms(db)

        profile = UserProfile(
            locale="en",
            interests=["general"],
            preferred_length="short",
        )

        day = date(2025, 1, 10)

        digest = build_daily_digest_for_user(
            db=db,
            user_id=user.id,
            day=day,
            user_profile=profile,
        )

        from app.text_generation import DailyDigestText

        assert isinstance(digest, DailyDigestText)
        assert digest.date == day
        assert digest.locale == "en"
        assert len(digest.body) > 0
        assert "entertainment" in digest.disclaimer.lower()
        assert digest.title
    finally:
        db.close()
