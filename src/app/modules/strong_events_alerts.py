from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.repo import session_scope
from app.astro_core import ensure_daily_transits

Atom = Dict[str, Any]

# минимальный порог «силы» транзита, чтобы считать его сильным
STRONG_THRESHOLD = 0.75


def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    """
    Собирает атомы для алертов по сильным астрособытиям.

    Логика:
      * берём транзиты из astro_core на окно в N дней (window_days)
      * для каждого дня выбираем события с strength >= STRONG_THRESHOLD
      * каждое событие -> Atom c topic_tag/weight (без текста)
      * текст позже подставит оркестратор через ContentAtom по topic_tag.
    """
    cfg = config or {}
    window_days = int(cfg.get("window_days", 3))

    today = datetime.utcnow().date()
    atoms: List[Atom] = []

    with session_scope() as db:
        for offset in range(window_days):
            day = today + timedelta(days=offset)
            events = ensure_daily_transits(db, user_ref=user_id, day=day)

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
                        # text намеренно не заполняем — мультиязычие через ContentAtom
                    }
                )

    # Фолбек, если ничего сильного не нашли в окне
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
