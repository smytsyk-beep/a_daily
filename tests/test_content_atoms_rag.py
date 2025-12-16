# tests/test_content_atoms_rag.py
from datetime import date, datetime, timezone

from app.db import SessionLocal
from app import models
from app.content_atoms_rag import (
    UserProfile,
    select_atoms_for_day,
)


def _make_user(db) -> models.User:
    user = db.query(models.User).filter(models.User.tg_user_id == "rag_user").first()
    if user:
        return user

    user = models.User(tg_user_id="rag_user", locale="en")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_birth_data(db, user_id: int):
    # Для транзитов/натала у нас уже есть инфраструктура,
    # здесь просто гарантируем, что есть birth_data с координатами.
    if db.query(models.BirthData).filter(models.BirthData.user_id == user_id).first():
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
    # Если уже есть хотя бы один атом с trigger="generic" — ничего не делаем
    existing = (
        db.query(models.ContentAtom)
        .filter(models.ContentAtom.trigger == "generic")
        .first()
    )
    if existing:
        return

    long_text = "This is a longer generic daily guidance text."

    atom = models.ContentAtom(
        locale="en",
        # старые поля, которые уже были в модели
        body=long_text,  # <-- ВАЖНО: заполняем NOT NULL поле
        topic_tag="generic",  # (если у тебя есть такое поле, можно тоже заполнить)
        style="neutral",  # (если поле style есть — не помешает)
        # новые поля матрицы
        trigger="generic",
        house_tags=["I"],
        persona_tags=["general"],
        strength_hint="light_to_medium",
        copy_short="Generic daily guidance.",
        copy_long=long_text,
        cta="Take a deep breath and plan your day.",
    )
    db.add(atom)
    db.commit()


def test_select_atoms_for_day_returns_atoms():
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

        today = date(2025, 1, 1)

        atoms = select_atoms_for_day(
            db=db,
            user_id=user.id,
            day=today,
            user_profile=profile,
            max_total_atoms=4,
        )

        # Должен вернуться хотя бы один атом
        assert len(atoms) >= 1
        # И у него должен быть связан ContentAtom
        first = atoms[0]
        assert first.atom is not None
        assert first.atom.locale == "en"
    finally:
        db.close()
