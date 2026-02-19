from datetime import date

import pytest

from app.geo import (
    GeoPoint,
    tz_by_latlon,
    resolve_place_to_coords_and_tz,
    build_utc_datetime_for_local_day,
)


def test_tz_by_latlon_known_cities():
    assert tz_by_latlon(40.7128, -74.0060) == "America/New_York"
    assert tz_by_latlon(34.0522, -118.2437) == "America/Los_Angeles"
    assert tz_by_latlon(51.5074, -0.1278) == "Europe/London"
    assert tz_by_latlon(50.4501, 30.5234) == "Europe/Kyiv"


def test_resolve_place_to_coords_and_tz_offline_map(monkeypatch):
    """resolve_place_to_coords_and_tz использует geocode (заглушка возвращает None); мокаем для проверки tz."""
    # Координаты Киева; geocode_place_nominatim в app.geo — заглушка (всегда None), поэтому мокаем
    stub_point = GeoPoint(50.4501, 30.5234, "Kyiv")
    monkeypatch.setattr(
        "app.geo.geocode_place_nominatim",
        lambda q: stub_point if q == "Kyiv" else None,
    )
    gp, tzid = resolve_place_to_coords_and_tz("Kyiv")
    assert gp is not None
    assert tzid == "Europe/Kyiv"


def test_build_utc_datetime_for_local_day():
    # Kyiv зимой UTC+2: 08:00 local -> 06:00 UTC
    dt_utc = build_utc_datetime_for_local_day(date(2025, 1, 15), "Europe/Kyiv", "08:00")
    assert dt_utc.isoformat() == "2025-01-15T06:00:00+00:00"

    # New York зимой UTC-5: 08:00 local -> 13:00 UTC
    dt_utc = build_utc_datetime_for_local_day(
        date(2025, 1, 15), "America/New_York", "08:00"
    )
    assert dt_utc.isoformat() == "2025-01-15T13:00:00+00:00"
