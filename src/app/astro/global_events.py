# src/app/astro/global_events.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Literal


GlobalEventKind = Literal["moon_phase", "ingress", "retrograde"]


@dataclass
class GlobalEvent:
    """
    Простая модель глобального астрособытия.

    В будущем сюда можно добавить:
    - знак, дом
    - участвующие планеты
    - человекочитаемый summary и т.п.
    """

    ts_utc: datetime
    kind: GlobalEventKind
    name: str
    payload: Dict[str, Any]


_PHASE_NAMES = [
    "New Moon",
    "First Quarter",
    "Full Moon",
    "Last Quarter",
]


def _daterange(start: date, end: date):
    """Итерируемся по датам включительно."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def compute_global_events(start: date, end: date) -> List[GlobalEvent]:
    """
    Stub-реализация глобальных событий (фазы Луны / ингрессии / ретроградности).

    Сейчас:
    - на каждый день диапазона отдаём по одному событию-фазе Луны;
    - имена фаз циклически берутся из _PHASE_NAMES;
    - всё помечено payload["stub"] = True, чтобы было видно, что это заглушка.

    Позже:
    - заменим на реальный расчёт через Skyfield;
    - добавим сюда ингрессии и ретроградности.
    """
    if end < start:
        raise ValueError("end must be >= start")

    events: List[GlobalEvent] = []

    for idx, day in enumerate(_daterange(start, end)):
        phase_name = _PHASE_NAMES[idx % len(_PHASE_NAMES)]
        ts_utc = datetime.combine(day, time(0, 0), tzinfo=timezone.utc)

        events.append(
            GlobalEvent(
                ts_utc=ts_utc,
                kind="moon_phase",
                name=phase_name,
                payload={
                    "phase": phase_name,
                    "stub": True,
                },
            )
        )

    return events
