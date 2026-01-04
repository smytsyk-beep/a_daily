from __future__ import annotations

from datetime import datetime, date, time, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app import models
from app.models import TransitEvent
from app.repo import resolve_user_id, get_birth_data
from app.astro import skyfield_client


def _day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """Возвращает (start_utc, end_utc) для суток в UTC."""
    start = datetime.combine(day, time(0, 0), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


# ================== Транзиты к наталу (stub) ==================


def get_daily_transits(
    db: Session,
    user_id: int,
    day: Optional[date] = None,
) -> List[TransitEvent]:
    """
    Возвращает все транзитные события пользователя за указанный день (UTC).
    Ничего не создаёт, просто читает из таблицы transit_events.
    """
    if day is None:
        day = datetime.utcnow().date()

    start, end = _day_bounds_utc(day)

    return (
        db.query(TransitEvent)
        .filter(
            TransitEvent.user_id == user_id,
            TransitEvent.ts_utc >= start,
            TransitEvent.ts_utc < end,
        )
        .order_by(TransitEvent.ts_utc)
        .all()
    )


def compute_daily_transits(
    db: Session,
    user_id: int,
    day: Optional[date] = None,
    bucket: str = "digest",
) -> List[TransitEvent]:
    """
    Stub-реализация расчёта транзитов на день.

    Финальная версия будет считать реальные аспекты к наталу через Skyfield,
    но уже сейчас у нас есть единая точка входа:

      * смотрим, есть ли транзиты на день;
      * если есть — просто возвращаем;
      * если нет — создаём один «generic» транзит посреди дня.
    """
    if day is None:
        day = datetime.utcnow().date()

    # 1. Если уже есть транзиты — используем их
    existing = get_daily_transits(db, user_id=user_id, day=day)
    if existing:
        return existing

    # 2. Иначе создаём временный generic-транзит (как раньше делал ensure_daily_transits)
    start, end = _day_bounds_utc(day)
    mid_ts = start + (end - start) / 2

    payload = {
        "module": "astro_core",
        "kind": "generic_day",
        "topic_tag": "generic_day_overview",
        "strength": 0.5,
        "source": "compute_daily_transits_stub",
    }

    ev = TransitEvent(
        user_id=user_id,
        ts_utc=mid_ts,
        kind="generic",
        payload=payload,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return [ev]


def ensure_daily_transits(
    db: Session,
    user_ref,
    day: Optional[date] = None,
    bucket: str = "digest",  # 👈 новый параметр с дефолтом
) -> List[TransitEvent]:
    """
    Высокоуровневый helper.

    - преобразует user_ref -> numeric user_id через resolve_user_id;
    - делегирует основную работу в compute_daily_transits.

    bucket:
      - "digest" — транзиты для дневного дайджеста,
      - "strong" — транзиты для сильных алертов (strong_events_alerts),
      - можно расширять дальше.

    Таким образом, вся остальная логика (дайджест, .ics и т.п.)
    ходит в единый сервис расчёта транзитов.
    """
    user_id = resolve_user_id(db, user_ref)
    return compute_daily_transits(
        db,
        user_id=user_id,
        day=day,
        bucket=bucket,  # 👈 прокидываем дальше
    )


# ================== Натальная карта + кэш ==================


def _birthdata_to_utc(bd: models.BirthData) -> datetime:
    """
    Собираем datetime рождения и переводим в UTC.

    - если birth_time пустой/кривой — берём 12:00;
    - если tz не распарсился — считаем, что время уже в UTC.
    """
    # время
    time_str = (bd.birth_time or "").strip() or "12:00"
    try:
        hh_str, mm_str = time_str.split(":", 1)
        hh, mm = int(hh_str), int(mm_str)
    except Exception:
        hh, mm = 12, 0

    local_dt = datetime.combine(bd.birth_date, time(hour=hh, minute=mm))

    # таймзона
    tz_name = bd.tz or "UTC"
    try:
        tzinfo = ZoneInfo(tz_name)
    except Exception:
        tzinfo = timezone.utc

    local_dt = local_dt.replace(tzinfo=tzinfo)
    return local_dt.astimezone(timezone.utc)


def get_or_compute_natal(
    db: Session,
    user_id: int,
    *,
    recalc: bool = False,
) -> dict:
    """
    Вернуть натальную карту пользователя как JSON-совместимый словарь.

    Логика:
    1. Если в NatalCache уже есть запись и recalc=False → вернуть её payload.
    2. Иначе:
       - берём BirthData;
       - считаем позиции планет через skyfield_client.compute_all_bodies;
       - сохраняем/обновляем запись в NatalCache;
       - возвращаем свежий payload.
    """
    # 1. Пытаемся взять из кэша
    cache = (
        db.query(models.NatalCache)
        .filter(models.NatalCache.user_id == user_id)
        .order_by(models.NatalCache.id.desc())
        .first()
    )
    if cache and not recalc:
        # кэш уже есть — просто возвращаем
        return cache.payload

    # 2. Нужны birth_data
    birth = get_birth_data(db, user_id=user_id)
    if not birth:
        raise ValueError(f"No birth data for user {user_id}")

    if birth.lat is None or birth.lon is None:
        raise ValueError(f"Birth coordinates missing for user {user_id}")

    dt_utc = _birthdata_to_utc(birth)

    # 3. Считаем позиции тел через skyfield_client
    positions = skyfield_client.compute_all_bodies(
        dt_utc=dt_utc,
        lat=birth.lat,
        lon=birth.lon,
    )

    # 4. Готовим JSON-совместимый payload
    bodies_payload: dict[str, dict[str, float | str]] = {}
    for name, bp in positions.items():
        # ожидаем BodyPosition, но оставляем защиту на всякий случай
        if isinstance(bp, skyfield_client.BodyPosition):
            bodies_payload[name] = {
                "lon": bp.lon,
                "lat": bp.lat,
                "distance_au": bp.distance_au,
                "sign": bp.sign,
                "sign_degree": bp.sign_degree,
            }
        else:
            # если тесты замокают compute_all_bodies чем-то своим — просто кладём как есть
            bodies_payload[name] = dict(bp)  # type: ignore[arg-type]

    payload: dict = {
        "dt_utc": dt_utc.isoformat(),
        "lat": birth.lat,
        "lon": birth.lon,
        "tz": birth.tz,
        "bodies": bodies_payload,
        # позже сюда же добавим ASC/MC, дома и т.д.
    }

    # 5. Обновляем/создаём запись в кэше
    if cache:
        cache.payload = payload
        cache.created_at = datetime.utcnow()
    else:
        cache = models.NatalCache(user_id=user_id, payload=payload)
        db.add(cache)

    db.commit()
    db.refresh(cache)

    return payload


def precompute_transits_range(
    db: Session,
    user_ref,
    start: date,
    *,
    days: int = 7,
) -> List[TransitEvent]:
    """
    Утилита под крон/worker: гарантирует, что в transit_events есть
    транзиты для пользователя на диапазон дней.

    Сейчас это тонкая обёртка над ensure_daily_transits (stub):
    - для каждого дня диапазона вызывает ensure_daily_transits,
      которая:
        * проверяет, есть ли уже записи в transit_events;
        * если нет — создаёт stub-транзит(ы) через compute_daily_transits.
    - возвращает плоский список всех TransitEvent за диапазон.

    Позже, когда появится реальный расчёт транзитов, поведение
    ensure_daily_transits / compute_daily_transits можно будет
    заменить без изменения этого интерфейса.
    """
    if days < 1:
        raise ValueError("days must be >= 1")

    result: List[TransitEvent] = []

    for offset in range(days):
        day = start + timedelta(days=offset)
        # user_ref может быть int/tg_user_id/None — как и в других местах
        day_events = ensure_daily_transits(db, user_ref=user_ref, day=day)
        result.extend(day_events)

    return result
