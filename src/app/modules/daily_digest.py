# src/app/modules/daily_digest.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import User
from app.repo import session_scope
from app.daily_digest_service import build_daily_digest_for_user

Atom = Dict[str, Any]


def _user_local_date_and_time_iso(
    user: User, now_utc: datetime
) -> tuple[datetime.date, str]:
    """
    Возвращает:
    - локальную дату пользователя;
    - ISO-строку локального времени (для логов / payload'а).

    Если таймзона не задана или битая — используем UTC.
    """
    tz_name = getattr(user, "timezone", None) or "UTC"

    if ZoneInfo is None:
        now_local = now_utc
    else:
        try:
            now_local = now_utc.astimezone(ZoneInfo(tz_name))
        except Exception:
            now_local = now_utc

    return now_local.date(), now_local.isoformat()


def _resolve_user(db: Session, user_ref: Union[int, str]) -> Optional[User]:
    """
    Разрешает user_ref в объект User.
    - int: внутренний users.id (из Telegram webhook)
    - str: tg_user_id (для оркестратора)
    """
    if isinstance(user_ref, int):
        return db.query(User).filter(User.id == user_ref).one_or_none()
    # tg_user_id как строка
    return db.query(User).filter(User.tg_user_id == str(user_ref)).one_or_none()


def compute(
    user_id: Union[int, str],
    config: Optional[dict] = None,
) -> List[Atom]:
    """
    Точка входа модуля `daily_digest` для оркестратора и Telegram.

    1. Открывает сессию БД.
    2. Разрешает user_id (int или tg_user_id) → объект User.
    3. Вычисляет локальную дату пользователя по его таймзоне.
    4. Вызывает build_daily_digest_for_user (план, интересы, транзиты, атомы).
    5. Оборачивает результат в Atom для оркестратора / Telegram.
    """
    now_utc = datetime.utcnow()

    with session_scope() as db:
        user = _resolve_user(db, user_id)
        if user is None:
            raise ValueError(f"User not found for id={user_id!r}")

        day_local, time_local_iso = _user_local_date_and_time_iso(user, now_utc)

        length = None
        if config and isinstance(config.get("length"), str):
            length = config["length"]

        digest = build_daily_digest_for_user(
            db=db,
            user=user,
            today=day_local,
            length=length,
        )

    atom: Atom = {
        "module": "daily_digest",
        "kind": "digest",
        "topic_tag": "generic_day_overview",
        "weight": 1.0,
        "time_local": time_local_iso,
        "date": digest.date.isoformat(),
        "locale": digest.locale,
        "length": digest.length,
        "title": digest.title,
        "body": digest.body,
        "affirmation": digest.affirmation,
        "disclaimer": digest.disclaimer,
    }

    return [atom]
