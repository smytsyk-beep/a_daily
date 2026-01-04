# tests/test_timezone_cities.py

from app.geo import tz_by_latlon


def test_tz_by_latlon_cities_smoke():
    assert tz_by_latlon(40.7128, -74.0060) in ("America/New_York", None)
    assert tz_by_latlon(34.0522, -118.2437) in ("America/Los_Angeles", None)
    assert tz_by_latlon(51.5074, -0.1278) in ("Europe/London", None)
    assert tz_by_latlon(50.4501, 30.5234) in ("Europe/Kyiv", None)
