# tests/test_global_events_stub.py
from datetime import date

from app.astro.global_events import compute_global_events, GlobalEvent


def test_compute_global_events_basic_range():
    start = date(2025, 1, 1)
    end = date(2025, 1, 3)

    events = compute_global_events(start, end)

    # по одному событию на день
    assert len(events) == 3
    assert all(isinstance(ev, GlobalEvent) for ev in events)

    dates = {ev.ts_utc.date() for ev in events}
    assert dates == {start, date(2025, 1, 2), end}

    # пока только фазы Луны и все помечены как stub
    assert all(ev.kind == "moon_phase" for ev in events)
    assert all(ev.payload.get("stub") is True for ev in events)


def test_compute_global_events_deterministic():
    start = date(2025, 1, 1)
    end = date(2025, 1, 5)

    events1 = compute_global_events(start, end)
    events2 = compute_global_events(start, end)

    # детерминированность по имени и времени
    assert [(e.name, e.ts_utc) for e in events1] == [
        (e.name, e.ts_utc) for e in events2
    ]
