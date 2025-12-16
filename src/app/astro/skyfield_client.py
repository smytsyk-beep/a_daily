# src/app/astro/skyfield_client.py
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Literal

from datetime import datetime, timezone

# ВАЖНО: этот модуль не импортируется нигде автоматически,
# поэтому отсутствие skyfield в окружении сейчас ничего не ломает.
# Когда дойдём до реальной интеграции — добавим пакет в requirements.
try:
    from skyfield.api import load, wgs84
except ImportError:  # мягкий фолбек, чтобы не падали импорт-тесты
    load = None  # type: ignore[assignment]
    wgs84 = None  # type: ignore[assignment]


BodyName = Literal[
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
]


ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


@dataclass
class BodyPosition:
    body: BodyName
    lon: float  # эклиптическая долгота 0..360
    lat: float  # эклиптическая широта
    distance_au: float
    sign: str
    sign_degree: float  # 0..30 внутри знака


DATA_DIR = Path(__file__).resolve().parent / "data"
# имя файла можно будет переопределить через env позже
EPHEMERIS_FILE = DATA_DIR / "de440s.bsp"


def _require_skyfield() -> None:
    if load is None or wgs84 is None:
        raise RuntimeError(
            "skyfield не установлен. "
            "Добавь пакет 'skyfield' в зависимости приложения."
        )


@lru_cache(maxsize=1)
def get_ephemeris():
    """
    Ленивая загрузка файла эфемерид.

    Ожидаем, что de440s.bsp уже лежит в /app/src/app/astro/data/
    и попадает в Docker-образ.
    """
    _require_skyfield()
    return load(str(EPHEMERIS_FILE))  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def get_timescale():
    _require_skyfield()
    return load.timescale()  # type: ignore[no-any-return]


def _to_utc(dt: datetime) -> datetime:
    """Гарантируем aware datetime в UTC."""
    if dt.tzinfo is None:
        # считаем, что это уже UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_body_position(
    body: BodyName,
    dt_utc: datetime,
    lat: float,
    lon: float,
) -> BodyPosition:
    """
    Позиция планеты/Луны в эклиптических координатах
    для заданного момента и точки на Земле.
    """

    _require_skyfield()
    eph = get_ephemeris()
    ts = get_timescale()

    dt_utc = _to_utc(dt_utc)
    t = ts.from_datetime(dt_utc)

    earth = eph["earth"]
    location = earth + wgs84.latlon(lat_degrees=lat, lon_degrees=lon)  # type: ignore[arg-type]

    sf_body = eph[body]
    astrometric = location.at(t).observe(sf_body)
    lon_el, lat_el, distance = astrometric.ecliptic_latlon()

    lon_deg = float(lon_el.degrees)
    lat_deg = float(lat_el.degrees)
    dist_au = float(distance.au)

    sign_index = int(lon_deg // 30) % 12
    sign = ZODIAC_SIGNS[sign_index]
    sign_degree = lon_deg % 30.0

    return BodyPosition(
        body=body,
        lon=lon_deg,
        lat=lat_deg,
        distance_au=dist_au,
        sign=sign,
        sign_degree=sign_degree,
    )


def compute_all_bodies(
    dt_utc: datetime,
    lat: float,
    lon: float,
) -> Dict[BodyName, BodyPosition]:
    """
    Удобный helper: вернуть словарь с позициями всех тел,
    которые нам нужны для натала.
    """

    bodies: list[BodyName] = [
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
    ]
    return {
        name: compute_body_position(name, dt_utc=dt_utc, lat=lat, lon=lon)
        for name in bodies
    }


__all__ = [
    "BodyName",
    "BodyPosition",
    "compute_body_position",
    "compute_all_bodies",
    "get_ephemeris",
    "get_timescale",
]
