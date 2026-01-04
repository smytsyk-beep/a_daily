# src/app/astro/transit_precompute.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.astro_core import ensure_daily_transits

Bucket = Literal["digest", "strong"]


@dataclass
class PrecomputeResult:
    """
    Результат прекомпьюта транзитов на диапазон дат.
    """

    user_id: int
    start_date: date
    end_date: date
    days_processed: int
    events_total: int


def precompute_transits_for_user(
    db: Session,
    user_ref: int | str,
    start_date: date,
    end_date: date,
    *,
    bucket: Bucket = "digest",
) -> PrecomputeResult:
    """
    Идемпотентный сервис:

    - идём от start_date до end_date включительно;
    - на каждый день вызываем ensure_daily_transits(...),
      который сам:
        * считает транзиты,
        * кладёт их в transit_events,
        * возвращает список моделей;
    - считаем, сколько всего событий получили.

    Параметр bucket сейчас просто прокидываем дальше в ensure_daily_transits,
    чтобы в будущем различать:
      - 'digest'  — события для дневного дайджеста;
      - 'strong'  — события для сильных алертов.
    """

    if end_date < start_date:
        raise ValueError("end_date must be >= start_date")

    days_processed = 0
    events_total = 0

    cur = start_date
    while cur <= end_date:
        events = ensure_daily_transits(
            db=db,
            user_ref=user_ref,
            day=cur,
            bucket=bucket,
        )
        events_total += len(events)
        days_processed += 1
        cur += timedelta(days=1)

    # на случай, если ensure_daily_transits внутри создаёт нового пользователя
    # и возвращает события по user.id, логически считаем, что user_ref уже
    # приведён к числовому id верхним слоем
    user_id = int(user_ref) if isinstance(user_ref, str) and user_ref.isdigit() else user_ref  # type: ignore[assignment]

    return PrecomputeResult(
        user_id=int(user_id),
        start_date=start_date,
        end_date=end_date,
        days_processed=days_processed,
        events_total=events_total,
    )
