# src/app/birth_geo_service.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.services.geo import geocode_place
from app.services.timezone import tz_by_latlon


@dataclass
class GeoResult:
    lat: float
    lon: float
    tz: str  # IANA tzid, например "Europe/Kyiv"


# Мини-офлайн карта городов / стран.
# Это можно расширять по мере надобности.
CITY_DB = {
    # Украина
    "kyiv ukraine": GeoResult(50.4501, 30.5234, "Europe/Kyiv"),
    "kiev ukraine": GeoResult(50.4501, 30.5234, "Europe/Kyiv"),
    # США
    "new york usa": GeoResult(40.7128, -74.0060, "America/New_York"),
    "new york united states": GeoResult(40.7128, -74.0060, "America/New_York"),
    "los angeles usa": GeoResult(34.0522, -118.2437, "America/Los_Angeles"),
    "los angeles united states": GeoResult(34.0522, -118.2437, "America/Los_Angeles"),
    # Великобритания
    "london uk": GeoResult(51.5074, -0.1278, "Europe/London"),
    "london united kingdom": GeoResult(51.5074, -0.1278, "Europe/London"),
    # Молдова
    "chisinau moldova": GeoResult(47.0105, 28.8638, "Europe/Chisinau"),
    "chișinău moldova": GeoResult(47.0105, 28.8638, "Europe/Chisinau"),
    # Турция
    "istanbul turkey": GeoResult(41.0082, 28.9784, "Europe/Istanbul"),
    # Испания (пример — можно расширять)
    "madrid spain": GeoResult(40.4168, -3.7038, "Europe/Madrid"),
    "barcelona spain": GeoResult(41.3874, 2.1686, "Europe/Madrid"),
}

COUNTRY_DB = {
    # Фоллбек по стране: берём столицу/типовой город
    "ukraine": GeoResult(50.4501, 30.5234, "Europe/Kyiv"),
    "ukraina": GeoResult(50.4501, 30.5234, "Europe/Kyiv"),
    "moldova": GeoResult(47.0105, 28.8638, "Europe/Chisinau"),
    "republic of moldova": GeoResult(47.0105, 28.8638, "Europe/Chisinau"),
    "turkey": GeoResult(41.0082, 28.9784, "Europe/Istanbul"),
    "türkiye": GeoResult(41.0082, 28.9784, "Europe/Istanbul"),
    "usa": GeoResult(40.7128, -74.0060, "America/New_York"),
    "united states": GeoResult(40.7128, -74.0060, "America/New_York"),
    "united states of america": GeoResult(40.7128, -74.0060, "America/New_York"),
    "spain": GeoResult(40.4168, -3.7038, "Europe/Madrid"),
}


def _normalize(s: str) -> str:
    """
    Простейшая нормализация: нижний регистр, убираем лишние пробелы.
    """
    s = (s or "").strip().lower()
    s = s.replace("ё", "е")
    # убираем запятые и лишние пробелы
    s = s.replace(",", " ")
    parts = [p for p in s.split() if p]
    return " ".join(parts)


def resolve_place_to_geo(place: str) -> Optional[GeoResult]:
    """
    Мягкий офлайн-резолвер места рождения → (lat, lon, tz).

    Алгоритм:
      1) Нормализуем строку.
      2) Пытаемся маппить по городам (CITY_DB, по подстроке).
      3) Если не нашли — берём последний токен как страну и ищем в COUNTRY_DB.
    """
    if not place:
        return None

    norm = _normalize(place)

    # 1. Поиск по городам (подстрока)
    for key, geo in CITY_DB.items():
        if key in norm:
            return geo

    # 2. Попытка выделить страну как последний фрагмент
    raw_parts = [p.strip() for p in place.split(",") if p.strip()]
    if raw_parts:
        country_raw = raw_parts[-1]
        country_norm = _normalize(country_raw)
        if country_norm in COUNTRY_DB:
            return COUNTRY_DB[country_norm]

    # 3. fallback: попробуем взять последний токен norm
    tokens = norm.split()
    if tokens:
        last = tokens[-1]
        if last in COUNTRY_DB:
            return COUNTRY_DB[last]

    return None


def ensure_birthdata_geo_for_user(db: Session, user: models.User) -> None:
    """
    Гарантирует, что у BirthData для данного user есть lat/lon (и по возможности tz).

    Логика:
      1) Берём последнюю запись BirthData по user.id.
      2) Если lat/lon уже есть → ничего не делаем.
      3) Если place пустой → выходим.
      4) Через geocode_place(place) получаем lat/lon.
      5) При необходимости через tz_by_latlon(lat, lon) пытаемся получить tz.
      6) Сохраняем изменения в БД.

    ВАЖНО: user.timezone здесь НЕ трогаем — это отдельная настройка
    “таймзона доставки”, чтобы не смешивать смыслы.
    """
    birth: Optional[models.BirthData] = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user.id)
        .order_by(models.BirthData.id.desc())
        .first()
    )

    if not birth:
        print(f"[GEO] No BirthData for user_id={user.id}")
        return

    if birth.lat is not None and birth.lon is not None:
        # Координаты уже есть — считаем, что всё ок.
        # (tz можем добавить отдельно, если очень нужно.)
        return

    place = birth.place or ""
    if not place:
        print(f"[GEO] BirthData has empty place for user_id={user.id}")
        return

    geo = geocode_place(place)
    if not geo:
        print(
            f"[GEO] Could not geocode birth place for user_id={user.id}, "
            f"place={place!r}"
        )
        return

    birth.lat = geo.lat
    birth.lon = geo.lon

    # tz — по возможности через timezonefinder
    if not birth.tz:
        tz = tz_by_latlon(geo.lat, geo.lon)
        if tz:
            birth.tz = tz

    db.add(birth)
    db.commit()
    db.refresh(birth)

    print(
        f"[GEO] BirthData updated for user_id={user.id}: "
        f"lat={birth.lat}, lon={birth.lon}, tz={birth.tz}, place={place!r}"
    )
