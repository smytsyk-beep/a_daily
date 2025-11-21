# tests/test_content_atoms_repo.py
import pytest
from sqlalchemy import insert

from app import models, repo
from app.db import SessionLocal


@pytest.fixture
def db_session():
    """Простая фикстура сессии БД для тестов."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.rollback()
        db.close()


def test_get_content_atom_exact_locale(db_session):
    db = db_session

    db.execute(
        insert(models.ContentAtom).values(
            locale="en",
            topic_tag="transit_sun_conj_moon",
            style="neutral",
            body="Sun conjunct Moon (EN)",
        )
    )
    db.commit()

    atom = repo.get_content_atom(
        db=db,
        topic_tag="transit_sun_conj_moon",
        locale="en",
    )

    assert atom is not None
    assert atom.body == "Sun conjunct Moon (EN)"


def test_get_content_atom_fallback_locale(db_session):
    db = db_session

    db.execute(
        insert(models.ContentAtom).values(
            locale="en",
            topic_tag="transit_sun_conj_moon",
            style="neutral",
            body="Sun conjunct Moon (EN)",
        )
    )
    db.commit()

    atom = repo.get_content_atom(
        db=db,
        topic_tag="transit_sun_conj_moon",
        locale="es",
        fallback_locale="en",
    )

    assert atom is not None
    assert atom.locale == "en"
    assert "EN" in atom.body
