# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import User, EventFeedback
from app.repo import _get_or_create_user  # ок для внутреннего теста
import json

client = TestClient(app)


def test_seed_users_present_and_idempotent():
    """system/demo существуют, резолв не плодит дублей."""
    db = SessionLocal()
    try:
        # system с фиксированным id=1
        sysu = db.get(User, 1)
        assert sysu is not None and sysu.tg_user_id == "system"

        # demo по tg_user_id
        demo = db.query(User).filter(User.tg_user_id == "demo").first()
        assert demo is not None
        demo_id_before = demo.id

        # повторный резолв по алиасу — тот же id
        resolved_id = _get_or_create_user(db, "demo")
        assert resolved_id == demo_id_before

        # и по числовому id — тот же id
        resolved_id_num = _get_or_create_user(db, demo_id_before)
        assert resolved_id_num == demo_id_before
    finally:
        db.close()


def test_feedback_resolves_numeric_and_alias_user_ids():
    r1 = client.post(
        "/events/feedback", json={"user_id": "demo", "score": 4, "note": "via-alias"}
    )
    assert r1.status_code == 200 and r1.json().get("ok") is True

    r2 = client.post(
        "/events/feedback", json={"user_id": 1, "score": 5, "note": "via-numeric"}
    )
    assert r2.status_code == 200 and r2.json().get("ok") is True

    db = SessionLocal()
    try:
        rows = db.query(EventFeedback).order_by(EventFeedback.id.desc()).limit(2).all()
        assert len(rows) == 2

        last, prev = rows[0], rows[1]
        demo = db.query(User).filter(User.tg_user_id == "demo").first()
        assert demo is not None

        assert {last.user_id, prev.user_id} == {1, demo.id}

        def pick_note(s: str) -> str:
            try:
                obj = json.loads(s)
                if isinstance(obj, dict) and "note" in obj:
                    return str(obj["note"])
            except Exception:
                pass
            return s

        notes = {pick_note(last.note), pick_note(prev.note)}
        assert "via-alias" in notes and "via-numeric" in notes
    finally:
        db.close()
