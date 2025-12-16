# src/app/geo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoPoint:
    """
    Результат геокодинга (Nominatim и т.п.).
    Пока это просто структура данных — реальный HTTP добавим позже.
    """

    lat: float
    lon: float
    display_name: Optional[str] = None


def geocode_place_nominatim(query: str) -> Optional[GeoPoint]:
    """
    STUB под будущую интеграцию с Nominatim.

    Сейчас НИЧЕГО не вызывает извне и просто возвращает None,
    чтобы:
      * тесты были детерминированными,
      * в CI не требовались внешние HTTP-запросы и дополнительные пакеты.

    Дальше сюда добавим реальный запрос к Nominatim или локальный кэш.
    """
    # TODO: реальный вызов Nominatim с кэшем.
    _ = query  # чтобы линтер не ругался
    return None


def tz_by_latlon(lat: float, lon: float) -> Optional[str]:
    """
    STUB под timezonefinder (офлайн определение таймзоны по координатам).

    Сейчас:
      * не требует никаких внешних зависимостей;
      * всегда возвращает None (т.е. таймзону не знаем);
      * главное — стабильный интерфейс и отсутствие исключений.

    Позже сюда можно будет добавить:

        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        return tf.timezone_at(lat=lat, lng=lon)

    но это уже шаг следующего уровня.
    """
    _ = (lat, lon)
    return None
