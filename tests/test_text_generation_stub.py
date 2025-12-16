# tests/test_text_generation_stub.py
from datetime import date

from app import models
from app.content_atoms_rag import SelectedAtom, UserProfile
from app.text_generation import render_daily_digest_from_atoms, DailyDigestText


def _make_dummy_atom() -> models.ContentAtom:
    atom = models.ContentAtom(
        locale="en",
        body="Base body text.",
        topic_tag="generic_day",
        style="neutral",
        trigger="generic",
        house_tags=["I"],
        persona_tags=["general"],
        strength_hint="light_to_medium",
        copy_short="Short guidance text.",
        copy_long="Longer, more detailed guidance text for the day.",
        cta="Pause for a moment and set a gentle intention.",
    )
    return atom


def test_render_daily_digest_from_atoms_short():
    atom = _make_dummy_atom()
    sel = SelectedAtom(atom=atom, score=1.0)

    profile = UserProfile(
        locale="en",
        interests=["general"],
        preferred_length="short",
    )
    day = date(2025, 1, 1)

    digest = render_daily_digest_from_atoms(
        atoms=[sel],
        day=day,
        user_profile=profile,
        length_override=None,
    )

    assert isinstance(digest, DailyDigestText)
    assert digest.date == day
    assert digest.length == "short"
    assert "Short guidance" in digest.body
    assert "entertainment" in digest.disclaimer.lower()
    assert digest.affirmation is not None
    assert digest.title  # не пустой


def test_render_daily_digest_from_atoms_fallback_when_no_atoms():
    profile = UserProfile(locale="en", interests=["general"], preferred_length="medium")
    day = date(2025, 1, 2)

    digest = render_daily_digest_from_atoms(
        atoms=[],
        day=day,
        user_profile=profile,
    )

    assert digest.date == day
    assert digest.length == "medium"
    assert len(digest.body) > 0
    assert "entertainment" in digest.disclaimer.lower()


def test_render_daily_digest_deterministic():
    atom = _make_dummy_atom()
    sel = SelectedAtom(atom=atom, score=1.0)
    day = date(2025, 1, 3)
    profile = UserProfile(locale="en", interests=["general"], preferred_length="medium")

    d1 = render_daily_digest_from_atoms([sel], day, profile)
    d2 = render_daily_digest_from_atoms([sel], day, profile)

    assert d1.title == d2.title
    assert d1.body == d2.body
    assert d1.affirmation == d2.affirmation
