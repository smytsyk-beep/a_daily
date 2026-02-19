# src/app/services/geo.py
"""
DEPRECATED: этот модуль устарел.

Используйте вместо него:
    from app.services.geocoder import get_geocoder_service
    
    geocoder = get_geocoder_service(db, mode="chain")
    result = geocoder.geocode("Киев, Украина", language="ru")

Файл сохранён только для обратной совместимости со старыми импортами.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoResult:
    """
    DEPRECATED: используйте app.services.geocoder.GeoResult
    
    Результат геокодинга места:
    - lat / lon — координаты
    - display_name — человекочитаемое имя (можно показывать в UI/логах)
    """
    lat: float
    lon: float
    display_name: str


def geocode_place(query: str) -> Optional[GeoResult]:
    """
    DEPRECATED: используйте app.services.geocoder вместо этого.
    
    Старая функция геокодирования.
    Сохранена для обратной совместимости, но возвращает None.
    
    В новом коде используйте:
        from app.services.geocoder import get_geocoder_service
        from app.db import get_db
        
        db = next(get_db())
        geocoder = get_geocoder_service(db, mode="chain")
        result = geocoder.geocode(place, language="en")
    """
    # Возвращаем None, чтобы старый код переключился на новый geocoder
    return None
