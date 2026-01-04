# src/app/repo.py
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, date
from typing import Any, Generator, Optional, Union, List

from sqlalchemy import desc, text, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app import models
from app.models import User, ModuleRegistry, EventFeedback
from app.geo import tz_by_latlon, geocode_place_nominatim

DEFAULT_LOCALE = "en"
UserRef = Optional[Union[str, int]]


def get_session() -> Generator[Session, None, None]:
    """
    Генератор сессии для FastAPI Depends:
        db = next(get_session())
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Контекст менеджер с rollback при исключениях.
        with session_scope() as db:
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
        # commit делаем в функциях-операциях точечно, чтобы не было неожиданных коммитов
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _bump_users_seq(db: Session) -> None:
    """
    Выравниваем users_id_seq на MAX(id), если тесты/код создают пользователей с ручным id.
    Безопасно: если sequence нет/не Postgres — просто игнорируем.
    """
    try:
        db.execute(
            text(
                "SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users), true)"
            )
        )
    except Exception:
        pass


def _get_or_create_user(db: Session, user_ref: UserRef) -> int:
    """
    Возвращает users.id. Создаёт пользователя, если нужно.

    - user_ref=None -> системный пользователь id=1 (tg_user_id='system')
    - число / строка-число -> считаем, что это id, создаём (tg_user_id=str(id))
    - строка -> tg_user_id
    """
    # system user
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
            # важно: tg_user_id должен быть уникальным
            u = User(id=uid, tg_user_id=str(uid), locale=DEFAULT_LOCALE)
            db.add(u)
            db.flush()
            _bump_users_seq(db)
        return uid

    # alias tg_user_id
    alias = str(user_ref)
    u = db.query(User).filter(User.tg_user_id == alias).first()
    if not u:
        u = User(tg_user_id=alias, locale=DEFAULT_LOCALE)
        db.add(u)
        db.flush()
        db.refresh(u)
    return u.id


def resolve_user_id(db: Session, user_ref: UserRef) -> int:
    """
    Унифицированное разрешение user_ref → users.id.
    Оставляем для совместимости со всем проектом/тестами.
    """
    return _get_or_create_user(db, user_ref)


# ---------------------------------------------------------------------------
# Modules registry
# ---------------------------------------------------------------------------


def list_enabled_modules(db: Session) -> List[ModuleRegistry]:
    return (
        db.query(ModuleRegistry)
        .filter(ModuleRegistry.enabled.is_(True))
        .order_by(ModuleRegistry.module)
        .all()
    )


def ensure_default_modules(db: Session) -> None:
    """
    Идемпотентно гарантирует наличие базовых модулей.
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
    db.expire_all()


# ---------------------------------------------------------------------------
# Events / feedback logging
# ---------------------------------------------------------------------------


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


def list_recent_events(db: Session, limit: int = 20) -> List[EventFeedback]:
    return (
        db.query(EventFeedback)
        .order_by(EventFeedback.created_at.desc())
        .limit(limit)
        .all()
    )


def log_event(
    db: Session,
    event: str,
    user_id: UserRef = None,
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


# ---------------------------------------------------------------------------
# Content atoms
# ---------------------------------------------------------------------------


def get_content_atom(
    db: Session,
    topic_tag: str,
    locale: str,
    fallback_locale: str = "en",
) -> Optional[models.ContentAtom]:
    """
    Возвращает ContentAtom по topic_tag и локали с фолбеком на fallback_locale.
    """
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


# ---------------------------------------------------------------------------
# BirthData helpers
# ---------------------------------------------------------------------------


def get_birth_data(db: Session, user_id: int) -> Optional[models.BirthData]:
    """
    Возвращает последнюю запись BirthData для пользователя, если есть.
    """
    return (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user_id)
        .order_by(models.BirthData.id.desc())
        .first()
    )


def upsert_birth_data(
    db: Session,
    user_ref: UserRef = None,
    birth_date: date | None = None,
    birth_time: Optional[str] = None,
    place: str | None = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz: Optional[str] = None,
    *,
    user_id: Optional[int] = None,
) -> models.BirthData:
    """
    Создаёт или обновляет BirthData для пользователя.

    Дополнения (п.3.2):
    - если lat/lon не переданы, но place есть -> пробуем geocode_place_nominatim(place)
      (сейчас в geo.py stub вернёт None — это нормально)
    - если tz не передан, но есть lat/lon -> пробуем tz_by_latlon(lat, lon) (stub -> None)
    """
    if birth_date is None:
        raise ValueError("birth_date is required")

    # 1) Определяем пользователя
    if user_id is None:
        user_id = _get_or_create_user(db, user_ref)

    # 2) Геокодинг (если координат нет, но есть place)
    effective_lat, effective_lon = lat, lon
    if (effective_lat is None or effective_lon is None) and place:
        try:
            gp = geocode_place_nominatim(place)
            if gp:
                effective_lat, effective_lon = gp.lat, gp.lon
        except Exception:
            # никаких падений из-за гео-слоя
            pass

    # 3) Таймзона по координатам
    effective_tz = tz
    if effective_tz is None and effective_lat is not None and effective_lon is not None:
        try:
            effective_tz = tz_by_latlon(float(effective_lat), float(effective_lon))
        except Exception:
            pass

    # 4) Ищем последнюю запись BirthData
    bd = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user_id)
        .order_by(models.BirthData.id.desc())
        .first()
    )

    # 5) Создаём или обновляем
    if bd is None:
        bd = models.BirthData(
            user_id=user_id,
            birth_date=birth_date,
            birth_time=birth_time,
            tz=effective_tz,
            place=place,
            lat=effective_lat,
            lon=effective_lon,
        )
        db.add(bd)
    else:
        bd.birth_date = birth_date
        bd.birth_time = birth_time
        bd.tz = effective_tz
        bd.place = place
        bd.lat = effective_lat
        bd.lon = effective_lon

    db.commit()
    db.refresh(bd)
    return bd


__all__ = [
    "DEFAULT_LOCALE",
    "get_session",
    "session_scope",
    "resolve_user_id",
    "list_enabled_modules",
    "ensure_default_modules",
    "get_content_atom",
    "recent_events",
    "list_recent_events",
    "log_event",
    "get_birth_data",
    "upsert_birth_data",
]
