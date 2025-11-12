from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Union, Generator
import json

from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, ModuleRegistry, EventFeedback  # <-- User, EventFeedback

DEFAULT_LOCALE = "en"

def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a live SQLAlchemy Session and closes it after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def session_scope() -> Session:
    """
    Для внутреннего кода, где хочется писать: `with session_scope() as db: ...`
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """FastAPI dependency: yield real Session, not contextmanager."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _bump_users_seq(db: Session):
    db.execute(text(
        "SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id),1) FROM users), true)"
    ))


def list_enabled_modules(db: Session):
    return (
        db.query(ModuleRegistry)
        .filter(ModuleRegistry.enabled.is_(True))
        .order_by(ModuleRegistry.module)
        .all()
    )


def recent_events(
    db: Session,
    limit: int = 20,
    user_id: Optional[Union[str, int]] = None,
    event: Optional[str] = None,
) -> list[EventFeedback]:
    q = db.query(EventFeedback).order_by(desc(EventFeedback.created_at))

    # фильтр по событию
    if event:
        q = q.filter(EventFeedback.event_ref == event)

    # фильтр по пользователю (числовой id или tg_user_id)
    if user_id is not None:
        if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
            uid = int(user_id)
        else:
            u = db.query(User).filter(User.tg_user_id == str(user_id)).first()
            if not u:
                return []  # alias не найден — отдаём пусто
            uid = u.id
        q = q.filter(EventFeedback.user_id == uid)

    return q.limit(limit).all()


"""
def recent_events(db: Session, limit: int = 20) -> list[EventFeedback]:
    return (
        db.query(EventFeedback)
        .order_by(desc(EventFeedback.created_at))
        .limit(limit)
        .all()
    )
"""

def _get_or_create_user(db: Session, user_ref: Optional[Union[str, int]]) -> int:
    # system
    if user_ref is None:
        u = db.get(User, 1)
        if not u:
            u = User(id=1, tg_user_id="system", locale=DEFAULT_LOCALE)
            db.add(u)
            db.flush()
            _bump_users_seq(db)   # << вот здесь
        return 1

    # числовой id
    if isinstance(user_ref, int) or (isinstance(user_ref, str) and user_ref.isdigit()):
        uid = int(user_ref)
        u = db.get(User, uid)
        if not u:
            u = User(id=uid, tg_user_id=str(uid), locale=DEFAULT_LOCALE)
            db.add(u)
            db.flush()
            _bump_users_seq(db)   # << и здесь
        return uid

    # alias -> tg_user_id (без явного id — sequence работает сама)
    alias = str(user_ref)
    u = db.query(User).filter(User.tg_user_id == alias).first()
    if not u:
        u = User(tg_user_id=alias, locale=DEFAULT_LOCALE)
        db.add(u)
        db.flush()
        db.refresh(u)
    return u.id


def log_event(
    db: Session,
    event: str,
    user_id: Optional[Union[str, int]] = None,
    score: Optional[int] = None,
    payload: Optional[dict] = None,
) -> EventFeedback:
    """
    Логирует событие в EventFeedback. Делает единый commit.
    """
    uid = _get_or_create_user(db, user_id)

    note = (
        json.dumps(payload, ensure_ascii=False)
        if isinstance(payload, dict)
        else (payload or None)
    )

    ev = EventFeedback(
        user_id=uid,
        event_ref=event,
        score=score,
        note=note,
        created_at=datetime.utcnow(),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_recent_events(db: Session, limit: int = 20):
    return (
        db.query(EventFeedback)
        .order_by(EventFeedback.created_at.desc())
        .limit(limit)
        .all()
    )