# src/app/astro/natal.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, time, timezone
from typing import Dict, Any, Optional

from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models import BirthData, NatalCache
from app.astro.skyfield_client import compute_all_bodies, BodyPosition


@dataclass
class NatalChart:
    """Простая структура для натальной карты."""

    computed_at: datetime
    bodies: Dict[str, BodyPosition]
    # TODO: asc, mc, дома и т.п.


def _build_birth_datetime_utc(birth: BirthData) -> datetime:
    """
    Собираем aware datetime в UTC на основе birth_date + birth_time + tz.

    Правила:
    - если birth_time нет → считаем 12:00;
    - если tz задана и валидна (IANA, напр. "Europe/Berlin") →
      считаем, что дата/время заданы в этой зоне и переводим в UTC;
    - если tz пустая или некорректная → считаем, что это уже UTC.
    """
    # 1) локальное время рождения
    if birth.birth_time:
        hh, mm = map(int, birth.birth_time.split(":"))
        t = time(hh, mm)
    else:
        # по умолчанию полдень, чтобы не уезжали сильно аспекты
        t = time(12, 0)

    naive_local = datetime.combine(birth.birth_date, t)

    # 2) применяем таймзону, если она есть
    if birth.tz:
        try:
            tzinfo = ZoneInfo(birth.tz)
            local_dt = naive_local.replace(tzinfo=tzinfo)
            return local_dt.astimezone(timezone.utc)
        except Exception:
            # если tz кривая / нет в базе — fallback на "уже UTC"
            pass

    # считаем, что это уже UTC
    return naive_local.replace(tzinfo=timezone.utc)


def compute_natal_chart_for_birth(birth: BirthData) -> NatalChart:
    """
    Чистая функция: берёт BirthData и возвращает структуру с позициями планет.
    """
    if birth.lat is None or birth.lon is None:
        raise ValueError("BirthData must have lat & lon to compute natal chart")

    dt_utc = _build_birth_datetime_utc(birth)

    bodies = compute_all_bodies(
        dt_utc=dt_utc,
        lat=float(birth.lat),
        lon=float(birth.lon),
    )
    return NatalChart(
        computed_at=datetime.utcnow(),
        bodies=bodies,
    )


def serialize_natal(chart: NatalChart) -> dict[str, Any]:
    """Подготовка к сохранению в JSON."""
    return {
        "computed_at": chart.computed_at.isoformat(),
        "bodies": {
            name: {
                **asdict(pos),
            }
            for name, pos in chart.bodies.items()
        },
    }


def deserialize_natal(payload: dict[str, Any]) -> NatalChart:
    bodies: Dict[str, BodyPosition] = {}
    for name, pos in payload["bodies"].items():
        bodies[name] = BodyPosition(**pos)  # type: ignore[arg-type]

    computed_at = datetime.fromisoformat(payload["computed_at"])
    return NatalChart(computed_at=computed_at, bodies=bodies)


def get_or_compute_natal(
    db: Session,
    birth: BirthData,
    max_age_hours: int = 24 * 365,
) -> NatalChart:
    """
    Берём натал из кэша, если он есть и не старше max_age_hours.
    Иначе пересчитываем и обновляем кэш.

    Предполагаем, что BirthData уже выбран для пользователя отдельно.
    """

    cache: Optional[NatalCache] = (
        db.query(NatalCache)
        .filter(NatalCache.user_id == birth.user_id)
        .order_by(NatalCache.created_at.desc())
        .first()
    )

    now = datetime.utcnow()

    if cache:
        try:
            payload = (
                json.loads(cache.payload)
                if isinstance(cache.payload, str)
                else cache.payload
            )
            chart = deserialize_natal(payload)
            age_hours = (now - chart.computed_at).total_seconds() / 3600.0
            if age_hours <= max_age_hours:
                return chart
        except Exception:
            # При любых проблемах с кэшем просто пересчитываем
            pass

    # Пересчёт
    chart = compute_natal_chart_for_birth(birth)
    payload = serialize_natal(chart)

    if cache:
        cache.payload = payload
        cache.created_at = now
    else:
        cache = NatalCache(
            user_id=birth.user_id,
            payload=payload,
            created_at=now,
        )
        db.add(cache)

    db.commit()
    db.refresh(cache)
    return chart
