from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Union, Generator, List
import json

from sqlalchemy import desc, text, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, ModuleRegistry, EventFeedback
from . import models

DEFAULT_LOCALE = "en"


def get_session() -> Generator[Session, None, None]:
    """
    Генератор сессии для использования через `next(get_session())` или
    в обёртке-контекст менеджере (например, в orchestrator.py).
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Удобный контекст-менеджер для внутренних задач:
        with session_scope() as db:
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _bump_users_seq(db: Session) -> None:
    # выравниваем последовательность users_id_seq на MAX(id) (минимум 1)
    db.execute(
        text(
            "SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users), true)"
        )
    )


def list_enabled_modules(db: Session) -> List[ModuleRegistry]:
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
) -> List[EventFeedback]:
    q = db.query(EventFeedback).order_by(desc(EventFeedback.created_at))

    if event:
        q = q.filter(EventFeedback.event_ref == event)

    if user_id is not None:
        # поддержка numeric id и alias (tg_user_id)
        if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
            uid = int(user_id)
        else:
            u = db.query(User).filter(User.tg_user_id == str(user_id)).first()
            if not u:
                return []
            uid = u.id
        q = q.filter(EventFeedback.user_id == uid)

    return q.limit(limit).all()


def _get_or_create_user(db: Session, user_ref: Optional[Union[str, int]]) -> int:
    # system
    if user_ref is None:
        u = db.get(User, 1)
        if not u:
            u = User(id=1, tg_user_id="system", locale=DEFAULT_LOCALE)
            db.add(u)
            db.flush()
            _bump_users_seq(db)
        return 1

    # numeric id
    if isinstance(user_ref, int) or (isinstance(user_ref, str) and user_ref.isdigit()):
        uid = int(user_ref)
        u = db.get(User, uid)
        if not u:
            u = User(id=uid, tg_user_id=str(uid), locale=DEFAULT_LOCALE)
            db.add(u)
            db.flush()
            _bump_users_seq(db)
        return uid

    # alias (tg_user_id), id авто-инкремент
    alias = str(user_ref)
    u = db.query(User).filter(User.tg_user_id == alias).first()
    if not u:
        u = User(tg_user_id=alias, locale=DEFAULT_LOCALE)
        db.add(u)
        db.flush()
        db.refresh(u)
    return u.id


def resolve_user_id(db: Session, user_ref: Optional[Union[str, int]]) -> int:
    """
    Публичная обёртка вокруг _get_or_create_user.
    Принимает numeric id или tg_user_id, возвращает внутренний user.id.
    """
    return _get_or_create_user(db, user_ref)


def log_event(
    db: Session,
    event: str,
    user_id: Optional[Union[str, int]] = None,
    score: Optional[int] = None,
    payload: Optional[dict] = None,
) -> EventFeedback:
    """
    Логируем событие в EventFeedback и коммитим.
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


def list_recent_events(db: Session, limit: int = 20) -> List[EventFeedback]:
    return (
        db.query(EventFeedback)
        .order_by(EventFeedback.created_at.desc())
        .limit(limit)
        .all()
    )


def ensure_default_modules(db: Session) -> None:
    """
    Идемпотентно гарантирует наличие базовых модулей.
    Делается через ORM, чтобы изменения всегда были видны новым сессиям.
    """
    defaults = [
        ("daily_digest", True, {}),
        ("strong_events_alerts", True, {}),
    ]

    for module_name, enabled, cfg in defaults:
        exists = (
            db.query(ModuleRegistry)
            .filter(ModuleRegistry.module == module_name)
            .first()
        )
        if not exists:
            db.add(ModuleRegistry(module=module_name, enabled=enabled, config=cfg))

    db.commit()
    # «протираем» кэш сессии (не обязательно, но полезно в тестах)
    db.expire_all()


def get_content_atom(
    db: Session,
    topic_tag: str,
    locale: str,
    fallback_locale: str = DEFAULT_LOCALE,
) -> Optional[models.ContentAtom]:
    """
    Возвращает ContentAtom по topic_tag и локали с фолбеком на fallback_locale.
    """

    # 1. пробуем локаль пользователя
    stmt = (
        select(models.ContentAtom)
        .where(
            models.ContentAtom.topic_tag == topic_tag,
            models.ContentAtom.locale == locale,
        )
        .limit(1)
    )
    atom = db.execute(stmt).scalar_one_or_none()
    if atom is not None:
        return atom

    # 2. фолбек, например на 'en'
    if fallback_locale and fallback_locale != locale:
        stmt_fallback = (
            select(models.ContentAtom)
            .where(
                models.ContentAtom.topic_tag == topic_tag,
                models.ContentAtom.locale == fallback_locale,
            )
            .limit(1)
        )
        return db.execute(stmt_fallback).scalar_one_or_none()

    return None


__all__ = [
    "get_session",
    "session_scope",
    "list_enabled_modules",
    "recent_events",
    "log_event",
    "list_recent_events",
    "ensure_default_modules",
    "get_content_atom",
    "resolve_user_id",
]
