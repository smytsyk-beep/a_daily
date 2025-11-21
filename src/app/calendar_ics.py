# src/app/calendar_ics.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Union, List

from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models import User, TransitEvent
from app.repo import (
    session_scope,
    resolve_user_id,
    get_content_atom,
    DEFAULT_LOCALE,
)


def _fmt_utc(dt: datetime) -> str:
    """Формат для iCal: UTC timestamp YYYYMMDDTHHMMSSZ."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _escape_ical(text: str) -> str:
    """Минимальный экранировщик для iCal."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def build_calendar_ics_for_user(
    db: Session,
    user_id: int,
    days_ahead: int = 7,
    tz_override: str | None = None,
) -> str:
    """
    Собирает строку .ics для пользователя.

    tz_override — если передан, используем эту таймзону вместо user.timezone.
    """
    user: User | None = db.get(User, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    locale = user.locale or DEFAULT_LOCALE
    tz_name = tz_override or user.timezone or "UTC"

    # валидируем tz_name через ZoneInfo, иначе падаем в UTC
    try:
        _ = ZoneInfo(tz_name)
    except Exception:
        tz_name = "UTC"

    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    end_utc = now_utc + timedelta(days=days_ahead)

    events: List[TransitEvent] = (
        db.query(TransitEvent)
        .filter(
            TransitEvent.user_id == user_id,
            TransitEvent.ts_utc >= now_utc.replace(tzinfo=None),
            TransitEvent.ts_utc <= end_utc.replace(tzinfo=None),
        )
        .order_by(TransitEvent.ts_utc)
        .all()
    )

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AstroDaily//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-TIMEZONE:{tz_name}",
    ]

    dtstamp = _fmt_utc(now_utc)

    for ev in events:
        payload = ev.payload or {}
        topic_tag = (
            payload.get("topic_tag") or payload.get("tag") or "generic_day_overview"
        )

        # текст берём из ContentAtom, если есть
        atom = get_content_atom(db, topic_tag=topic_tag, locale=locale)
        if atom:
            summary = atom.body
        else:
            summary = topic_tag

        summary = _escape_ical(str(summary))

        ts_utc = ev.ts_utc
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.replace(tzinfo=timezone.utc)

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ev.id}@astrodaily",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART:{_fmt_utc(ts_utc)}",
                f"SUMMARY:{summary}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def build_calendar_ics_for_user_ref(
    user_ref: Union[int, str],
    days_ahead: int = 7,
    tz: str | None = None,
) -> str:
    """
    Удобная обёртка: принимает user_id или tg_user_id.
    tz — опциональный override таймзоны (строка, например "Europe/Berlin").
    """
    with session_scope() as db:
        user_id = resolve_user_id(db, user_ref)
        return build_calendar_ics_for_user(
            db,
            user_id=user_id,
            days_ahead=days_ahead,
            tz_override=tz,
        )
