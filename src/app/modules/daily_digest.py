# src/app/modules/daily_digest.py
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from app.repo import session_scope
from app.astro_core import ensure_daily_transits

Atom = Dict[str, Any]


def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    """
    Собирает атомы для ежедневного дайджеста.

    Логика:
      * читаем транзиты на сегодня через astro_core.ensure_daily_transits
      * каждый TransitEvent превращаем в Atom с topic_tag/weight
      * текст НЕ заполняем — его потом подставит оркестратор через ContentAtom.
    """
    cfg = config or {}
    # пока просто прокидываем в атом, чтобы модуль доставки мог учитывать локальное время
    time_local = cfg.get("time_local", "08:00")

    today = datetime.utcnow().date()

    with session_scope() as db:
        events = ensure_daily_transits(db, user_ref=user_id, day=today)

    atoms: List[Atom] = []
    for ev in events:
        payload = ev.payload or {}

        topic_tag = (
            payload.get("topic_tag") or payload.get("tag") or "generic_day_overview"
        )
        strength = float(payload.get("strength", 1.0))

        atoms.append(
            {
                "module": "daily_digest",
                "kind": payload.get("kind", "digest"),
                "topic_tag": topic_tag,
                "weight": strength,
                "time_local": time_local,
                # text намеренно не заполняем — мультиязычие через ContentAtom
            }
        )

    # жёсткий фолбек, если ядро по какой-то причине вернуло пусто
    if not atoms:
        atoms = [
            {
                "module": "daily_digest",
                "kind": "digest",
                "topic_tag": "generic_day_overview",
                "weight": 1.0,
                "time_local": time_local,
            }
        ]

    return atoms
