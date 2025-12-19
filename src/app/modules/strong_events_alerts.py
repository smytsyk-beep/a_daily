from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.repo import session_scope
from app.astro.transit_service import compute_strong_alert_transits

from app import models

Atom = Dict[str, Any]

# сколько сильных аспектов показываем максимум на день
MAX_EVENTS_PER_DAY = 3


def _topic_tag_for_aspect(aspect: str) -> str:
    # можно расширять позже
    return {
        "conjunction": "strong_conjunction",
        "opposition": "strong_opposition",
        "square": "strong_square",
        "trine": "strong_trine",
        "sextile": "strong_sextile",
    }.get(aspect, "generic_strong_transit")


def _resolve_user_pk(db, user_ref: str) -> int | None:
    if isinstance(user_ref, str) and user_ref.isdigit():
        return int(user_ref)
    u = db.query(models.User).filter(models.User.tg_user_id == str(user_ref)).first()
    return u.id if u else None


def compute(user_id: str, config: dict | None = None) -> List[Atom]:

    cfg = config or {}
    window_days = int(cfg.get("window_days", 3))

    today = datetime.utcnow().date()
    atoms: List[Atom] = []

    with session_scope() as db:
        uid = _resolve_user_pk(db, user_id)
        if uid is None:
            # fallback если пользователя нет
            return [
                {
                    "module": "strong_events_alerts",
                    "kind": "alert",
                    "topic_tag": "generic_strong_transit_window",
                    "weight": 1.0,
                    "window_days": window_days,
                }
            ]

        for offset in range(window_days):
            day = today + timedelta(days=offset)
            try:
                # пока оставляем твой источник, либо замени на compute_strong_alert_transits
                events = ensure_daily_transits(db, user_ref=uid, day=day)
            except Exception:
                events = []

            for ev in events:
                payload = ev.payload or {}
                strength = float(payload.get("strength", 1.0))
                if strength < STRONG_THRESHOLD:
                    continue

                topic_tag = (
                    payload.get("topic_tag")
                    or payload.get("tag")
                    or "generic_strong_transit"
                )
                atoms.append(
                    {
                        "module": "strong_events_alerts",
                        "kind": "alert",
                        "topic_tag": topic_tag,
                        "weight": strength,
                        "day": day.isoformat(),
                        "window_days": window_days,
                    }
                )

    if not atoms:
        atoms = [
            {
                "module": "strong_events_alerts",
                "kind": "alert",
                "topic_tag": "generic_strong_transit_window",
                "weight": 1.0,
                "window_days": window_days,
            }
        ]

    return atoms
