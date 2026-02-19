# src/app/geo.py
"""
Утилиты для работы с географией и временем.

Содержит:
- Определение timezone по координатам (timezonefinder)
- Конвертация локального времени в UTC
- Устаревший geocode_place_nominatim (deprecated, используйте app.services.geocoder)
"""

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
    
    DEPRECATED: используйте app.services.geocoder.GeoResult вместо этого.
    """
    lat: float
    lon: float
    display_name: Optional[str] = None


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
    DEPRECATED: используйте app.services.geocoder вместо этого.
    
    Эта функция сохранена только для обратной совместимости с тестами.
    В новом коде используйте:
        from app.services.geocoder import get_geocoder_service
        geocoder = get_geocoder_service(db, mode="nominatim")
        result = geocoder.geocode(place, language="en")
    """
    # Минимальная заглушка для обратной совместимости
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
    DEPRECATED: используйте app.services.geocoder вместо этого.
    
    Сохранено для обратной совместимости с тестами.
    """
    gp = geocode_place_nominatim(place)
    if not gp:
        return None, None
    tzid = tz_by_latlon(gp.lat, gp.lon)
    return gp, tzid
