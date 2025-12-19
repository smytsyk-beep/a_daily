# src/app/astro/skyfield_client.py

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Literal, Optional

# Мягкий фолбек: чтобы импорт не ломал тесты, если skyfield не установлен.
try:
    from skyfield.api import Loader, wgs84
except ImportError:  # pragma: no cover
    Loader = None  # type: ignore[assignment]
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


@dataclass(frozen=True)
class BodyPosition:
    body: BodyName
    lon: float  # эклиптическая долгота 0..360
    lat: float  # эклиптическая широта
    distance_au: float
    sign: str
    sign_degree: float  # 0..30 внутри знака


def _require_skyfield() -> None:
    if Loader is None or wgs84 is None:
        raise RuntimeError(
            "skyfield не установлен. Добавь пакет 'skyfield' в зависимости приложения."
        )


def _project_root() -> Path:
    # .../src/app/astro/skyfield_client.py -> root = parents[3]
    return Path(__file__).resolve().parents[3]


def _norm_deg(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x


def _to_utc(dt: datetime) -> datetime:
    """Гарантируем aware datetime в UTC."""
    if dt.tzinfo is None:

        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _get_ephemeris_dir() -> Path:
    # По умолчанию: <repo>/data/ephemeris
    default_dir = _project_root() / "data" / "ephemeris"
    return Path(os.getenv("ASTRO_EPHEMERIS_DIR", str(default_dir)))


def _get_ephemeris_file() -> str:
    return os.getenv("ASTRO_EPHEMERIS_FILE", "de440s.bsp")


@lru_cache(maxsize=1)
def get_loader() -> "Loader":
    """
    Loader сам скачает *.bsp при первом вызове и будет использовать локальный кэш.
    """
    _require_skyfield()
    ephem_dir = _get_ephemeris_dir()
    ephem_dir.mkdir(parents=True, exist_ok=True)
    return Loader(str(ephem_dir))  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def get_ephemeris():
    """
    Автоскачивание и кэш эфемерид.
    Файл будет лежать в ASTRO_EPHEMERIS_DIR / ASTRO_EPHEMERIS_FILE.
    """
    loader = get_loader()
    return loader(_get_ephemeris_file())  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def get_timescale():
    loader = get_loader()
    return loader.timescale()  # type: ignore[no-any-return]


def compute_body_position(
    body: BodyName,
    dt_utc: datetime,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    *,
    topocentric: bool = False,
) -> BodyPosition:
    """
    Позиция тела в эклиптических координатах.

    По умолчанию: геоцентрическая (рекомендовано для базового натала/транзитов).
    Если topocentric=True — использует наблюдателя (lat/lon) и учитывает параллакс,
    что особенно заметно для Луны.
    """

    eph = get_ephemeris()
    ts = get_timescale()

    dt_utc = _to_utc(dt_utc)
    t = ts.from_datetime(dt_utc)

    earth = eph["earth"]

    BODY_TO_KERNEL = {
        "sun": "sun",
        "moon": "moon",
        "mercury": "mercury",
        "venus": "venus",
        "mars": "mars barycenter",
        "jupiter": "jupiter barycenter",
        "saturn": "saturn barycenter",
        "uranus": "uranus barycenter",
        "neptune": "neptune barycenter",
        "pluto": "pluto barycenter",
    }

    sf_body = eph[BODY_TO_KERNEL[body]]

    if topocentric:
        if lat is None or lon is None:
            raise ValueError("lat/lon обязательны при topocentric=True")
        observer = earth + wgs84.latlon(lat_degrees=lat, lon_degrees=lon)  # type: ignore[arg-type]
        astrometric = observer.at(t).observe(sf_body)
    else:
        astrometric = earth.at(t).observe(sf_body)

    apparent = astrometric.apparent()
    lat_el, lon_el, distance = apparent.ecliptic_latlon()

    lon_deg = _norm_deg(float(lon_el.degrees))
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
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    *,
    topocentric: bool = False,
) -> Dict[BodyName, BodyPosition]:

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
        name: compute_body_position(
            name, dt_utc=dt_utc, lat=lat, lon=lon, topocentric=topocentric
        )
        for name in bodies
    }


__all__ = [
    "BodyName",
    "BodyPosition",
    "compute_body_position",
    "compute_all_bodies",
    "get_ephemeris",
    "get_timescale",
    "get_loader",
]
