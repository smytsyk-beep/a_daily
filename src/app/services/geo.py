# src/app/services/geo.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class GeoResult:
    """
    Результат геокодинга места:
    - lat / lon — координаты
    - display_name — человекочитаемое имя (можно показывать в UI/логах)
    """

    lat: float
    lon: float
    display_name: str


def _normalize(s: str) -> str:
    """
    Простейшая нормализация строки места:
    - lower-case
    - убираем запятые и лишние пробелы
    - заменяем 'ё' → 'е'
    """
    s = (s or "").strip().lower()
    s = s.replace("ё", "е")
    s = s.replace(",", " ")
    parts = [p for p in s.split() if p]
    return " ".join(parts)


# Мини-офлайн база стран (и некоторых городов) → координаты.
# Это пока заглушка вместо реального Nominatim, но уже даёт внятный результат
# для типичных кейсов.
COUNTRY_DB: Dict[str, GeoResult] = {
    # Украина → Киев
    "ukraine": GeoResult(50.4501, 30.5234, "Kyiv, Ukraine"),
    "ukraina": GeoResult(50.4501, 30.5234, "Kyiv, Ukraine"),
    # Молдова → Кишинёв
    "moldova": GeoResult(47.0105, 28.8638, "Chisinau, Moldova"),
    "republic of moldova": GeoResult(47.0105, 28.8638, "Chisinau, Moldova"),
    # Турция → Стамбул (условно)
    "turkey": GeoResult(41.0082, 28.9784, "Istanbul, Turkey"),
    "türkiye": GeoResult(41.0082, 28.9784, "Istanbul, Turkey"),
    # США → Нью-Йорк (условно)
    "usa": GeoResult(40.7128, -74.0060, "New York, USA"),
    "united states": GeoResult(40.7128, -74.0060, "New York, USA"),
    "united states of america": GeoResult(40.7128, -74.0060, "New York, USA"),
    # Испания → Мадрид
    "spain": GeoResult(40.4168, -3.7038, "Madrid, Spain"),
}

CITY_DB: Dict[str, GeoResult] = {
    # Пара явных городов / вариантов написания
    "kyiv ukraine": GeoResult(50.4501, 30.5234, "Kyiv, Ukraine"),
    "kiev ukraine": GeoResult(50.4501, 30.5234, "Kyiv, Ukraine"),
    "chisinau moldova": GeoResult(47.0105, 28.8638, "Chisinau, Moldova"),
    "chișinău moldova": GeoResult(47.0105, 28.8638, "Chisinau, Moldova"),
    "los angeles usa": GeoResult(34.0522, -118.2437, "Los Angeles, USA"),
    "los angeles united states": GeoResult(34.0522, -118.2437, "Los Angeles, USA"),
    "new york usa": GeoResult(40.7128, -74.0060, "New York, USA"),
    "new york united states": GeoResult(40.7128, -74.0060, "New York, USA"),
    "london uk": GeoResult(51.5074, -0.1278, "London, UK"),
    "london united kingdom": GeoResult(51.5074, -0.1278, "London, UK"),
}


def geocode_place(query: str) -> Optional[GeoResult]:
    """
    Мягкий офлайн-геокодер места рождения.

    Алгоритм:
      1) Нормализуем строку.
      2) Пытаемся найти совпадение по CITY_DB (подстрокой).
      3) Если не нашли — берём последний "кусок" как страну и
         смотрим в COUNTRY_DB.
      4) Если всё равно нет — возвращаем None.

    Это заглушка поверх будущего вызова к Nominatim, но уже даёт
    адекватные координаты (хотя бы по стране/столице).
    """
    if not query:
        return None

    norm = _normalize(query)

    # 1. поиск по городам — ключ как подстрока
    for key, geo in CITY_DB.items():
        if key in norm:
            return geo

    # 2. попробуем выделить страну из последней части "City, Country"
    parts_raw = [p.strip() for p in query.split(",") if p.strip()]
    if parts_raw:
        country_raw = parts_raw[-1]
        country_norm = _normalize(country_raw)
        if country_norm in COUNTRY_DB:
            return COUNTRY_DB[country_norm]

    # 3. последний токен строки как fallback-страна
    tokens = norm.split()
    if tokens:
        last = tokens[-1]
        if last in COUNTRY_DB:
            return COUNTRY_DB[last]

    return None
