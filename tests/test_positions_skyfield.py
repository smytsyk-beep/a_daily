# tests/test_positions_skyfield.py

from datetime import datetime, timezone

from app.astro.skyfield_client import compute_all_bodies


def test_skyfield_positions_golden_values():
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    res = compute_all_bodies(dt)  # геоцентрически (topocentric=False по умолчанию)

    expected = {
        "sun": 295.238884,
        "moon": 134.337956,
        "mercury": 279.975481,
        "venus": 342.307994,
        "mars": 116.103993,
        "jupiter": 71.599281,
        "saturn": 345.402269,
        "uranus": 53.011954,
        "neptune": 357.203524,
        "pluto": 301.17199,
    }

    # Допуск: 0.01 градуса (~36 угл. секунд) — достаточно строго и стабильно для CI
    tol = 0.01

    for body, exp_lon in expected.items():
        got_lon = res[body].lon
        diff = abs(got_lon - exp_lon)
        assert (
            diff < tol
        ), f"{body}: got {got_lon:.6f}, expected {exp_lon:.6f}, diff {diff:.6f}"
