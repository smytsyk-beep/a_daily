# src/app/services/geo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoResult:
    lat: float
    lon: float
    display_name: str


def geocode_place(query: str) -> Optional[GeoResult]:
    """
    Заглушка поверх Nominatim.

    Позже сюда приедет реальный HTTP-запрос.
    Сейчас возвращаем None, чтобы явно было видно, что это stub.
    """
    return None
