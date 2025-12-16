# tests/test_geo_stubs.py
from app.geo import tz_by_latlon, geocode_place_nominatim, GeoPoint


def test_tz_by_latlon_stub_does_not_crash():
    tz = tz_by_latlon(55.75, 37.6)
    assert tz is None or isinstance(tz, str)


def test_geocode_place_stub_does_not_crash():
    res = geocode_place_nominatim("Moscow")
    assert res is None or isinstance(res, GeoPoint)
