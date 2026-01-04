# src/app/geo.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from functools import lru_cache
from typing import Optional

from zoneinfo import ZoneInfo

# timezonefinder — офлайн определение TZ по координатам
try:
    from timezonefinder import TimezoneFinder
except ImportError:  # pragma: no cover
    TimezoneFinder = None  # type: ignore[assignment]


@dataclass
class GeoPoint:
    """
    Результат геокодинга (Nominatim и т.п.).
    Сейчас используем детерминированную офлайн-карту для тестов/CI.
    """

    lat: float
    lon: float
    display_name: Optional[str] = None


# Детерминированная мапа для тестов/CI (без HTTP).
# В проде можно расширять/заменить на Nominatim + кэш.
_KNOWN_PLACES: dict[str, GeoPoint] = {
    "nyc": GeoPoint(40.7128, -74.0060, "New York City, NY, USA"),
    "new york": GeoPoint(40.7128, -74.0060, "New York City, NY, USA"),
    "los angeles": GeoPoint(34.0522, -118.2437, "Los Angeles, CA, USA"),
    "la": GeoPoint(34.0522, -118.2437, "Los Angeles, CA, USA"),
    "london": GeoPoint(51.5074, -0.1278, "London, UK"),
    "kyiv": GeoPoint(50.4501, 30.5234, "Kyiv, Ukraine"),
    "kiev": GeoPoint(50.4501, 30.5234, "Kyiv, Ukraine"),
}


_tf_singleton: Optional["TimezoneFinder"] = None


def _get_tf() -> Optional["TimezoneFinder"]:
    global _tf_singleton
    if TimezoneFinder is None:
        return None
    if _tf_singleton is None:
        _tf_singleton = TimezoneFinder()
    return _tf_singleton


def geocode_place_nominatim(query: str) -> Optional[GeoPoint]:
    """
    Пока без внешнего HTTP.
    Для тестов и CI используем локальную мапу _KNOWN_PLACES.

    Позже: добавим реальный Nominatim (httpx) + кэш и гибрид с Google.
    """
    q = (query or "").strip().lower()
    if not q:
        return None

    # 1) Детерминированный офлайн-слой
    if q in _KNOWN_PLACES:
        return _KNOWN_PLACES[q]

    # 2) Пока не делаем HTTP (безопасно для CI)
    return None


@lru_cache(maxsize=8192)
def _tz_cached(lat_r: float, lon_r: float) -> Optional[str]:
    """
    Внутренний кэшированный helper для timezonefinder.

    Ключ — округлённые координаты, чтобы не плодить записи
    при небольших плавающих отличиях.
    """
    tf = _get_tf()
    if tf is None:
        return None

    try:
        tzid = tf.timezone_at(lat=lat_r, lng=lon_r)
        return tzid or None
    except Exception:
        return None


def tz_by_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Офлайн TZ по координатам через timezonefinder.
    Возвращает IANA tzid, например "America/New_York".
    """
    # Округляем для стабильности и эффективного кэша (~10–11 м по широте)
    lat_r = round(float(lat), 4)
    lon_r = round(float(lon), 4)
    return _tz_cached(lat_r, lon_r)


def build_utc_datetime_for_local_day(
    day: date,
    tzid: str,
    time_hhmm: str | None,
) -> datetime:
    """
    day + time_hhmm в локальной TZ -> UTC aware datetime.

    Правила:
    - если time_hhmm нет -> 12:00
    - tzid обязан быть валидным IANA
    """
    if time_hhmm:
        hh, mm = map(int, time_hhmm.split(":"))
        t = time(hh, mm)
    else:
        t = time(12, 0)

    local_tz = ZoneInfo(tzid)
    local_dt = datetime.combine(day, t).replace(tzinfo=local_tz)
    return local_dt.astimezone(timezone.utc)


def resolve_place_to_coords_and_tz(
    place: str,
) -> tuple[Optional[GeoPoint], Optional[str]]:
    """
    place -> GeoPoint -> tzid
    """
    gp = geocode_place_nominatim(place)
    if not gp:
        return None, None
    tzid = tz_by_latlon(gp.lat, gp.lon)
    return gp, tzid
