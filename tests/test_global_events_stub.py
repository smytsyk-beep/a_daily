# tests/test_global_events_stub.py
from datetime import date, timedelta

from app.astro.global_events import compute_global_events


def test_compute_global_events_returns_one_per_day_and_stub_flag():
    start = date(2025, 1, 1)
    end = date(2025, 1, 5)  # 5 дней

    events = compute_global_events(start, end)

    # 5 дней → 5 событий
    assert len(events) == (end - start).days + 1

    # Даты и тип
    assert events[0].ts_utc.date() == start
    assert events[-1].ts_utc.date() == end
    assert all(e.kind == "moon_phase" for e in events)

    # Заглушка явно помечена
    assert all(e.payload.get("stub") is True for e in events)

    # Фазы циклично повторяются по диапазону
    names = [e.name for e in events]
    assert len(set(names)) >= 2  # хотя бы две разные фазы на диапазоне
