# tests/test_geo_stubs.py
"""
Тесты для обратной совместимости со старым geo модулем.

DEPRECATED: эти тесты сохранены для обратной совместимости.
Новый код должен использовать tests/test_geocoder.py.
"""
from app.geo import tz_by_latlon, geocode_place_nominatim, GeoPoint


def test_tz_by_latlon_stub_does_not_crash():
    """Проверка, что tz_by_latlon работает (если timezonefinder установлен)"""
    tz = tz_by_latlon(55.75, 37.6)
    # Может вернуть None если timezonefinder не установлен, или строку если установлен
    assert tz is None or isinstance(tz, str)


def test_geocode_place_stub_does_not_crash():
    """
    Проверка, что старый geocode_place_nominatim не падает.
    
    DEPRECATED: возвращает None, т.к. старая функция устарела.
    Используйте app.services.geocoder.get_geocoder_service вместо этого.
    """
    res = geocode_place_nominatim("Moscow")
    # Старая функция теперь возвращает None (deprecated)
    assert res is None or isinstance(res, GeoPoint)
