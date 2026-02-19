#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check which transits have events but no matching Russian atoms.
"""

from app.repo import session_scope
from app import models
from datetime import date, datetime, timezone

print("=" * 80)
print("MISSING RUSSIAN ATOMS FOR TODAY'S TRANSITS")
print("=" * 80)
print()

today = date(2026, 2, 18)
user_id = 2238

with session_scope() as db:
    # Get today's events
    day_start = datetime.combine(today, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    day_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

    events = (
        db.query(models.Event)
        .filter(
            models.Event.user_id == user_id,
            models.Event.ts >= day_start,
            models.Event.ts <= day_end,
        )
        .all()
    )

    print(f"Found {len(events)} events for {today}:")
    print()

    # Extract triggers from events
    triggers_from_events = set()
    for event in events:
        if event.details:
            transit_body = event.details.get("transit_body", "").lower()
            aspect = event.details.get("aspect", "").lower()
            natal_body = event.details.get("natal_body", "").lower()

            if transit_body and aspect and natal_body:
                trigger = f"{transit_body}_{aspect}_{natal_body}"
                triggers_from_events.add(trigger)
                print(f"  Event trigger: {trigger}")

    print()
    print(f"Unique triggers: {len(triggers_from_events)}")
    print()

    # Get all Russian atom triggers
    ru_atoms = (
        db.query(models.ContentAtom)
        .filter(
            models.ContentAtom.locale == "ru", models.ContentAtom.trigger.isnot(None)
        )
        .all()
    )

    triggers_in_atoms = set(atom.trigger for atom in ru_atoms if atom.trigger)

    print(f"Russian transit atoms available:")
    for trigger in sorted(triggers_in_atoms):
        print(f"  ✅ {trigger}")

    print()
    print("=" * 80)
    print("MISSING ATOMS")
    print("=" * 80)
    print()

    missing = triggers_from_events - triggers_in_atoms

    if missing:
        print(f"Found {len(missing)} triggers with NO Russian atoms:")
        for trigger in sorted(missing):
            print(f"  ❌ {trigger}")
        print()
        print("⚠️  These transits exist but system can't use them because")
        print("   there are no Russian content atoms for these triggers!")
    else:
        print("✅ All event triggers have matching Russian atoms")

    print()
    print("=" * 80)
    print("SOLUTION")
    print("=" * 80)
    print(
        """
To fix: Add more Russian transit atoms for common transits like:
- mars_trine_sun
- sun_square_mars
- saturn_trine_mars
- etc.

Currently we only have 10 transit atoms:
- sun_trine_moon (2)
- mercury_sextile_venus (2)
- mars_trine_jupiter
- mars_square_sun
- venus_square_mars
- mercury_square_neptune
- sun_square_saturn
- venus_conjunct_jupiter

We need at least 20-30 more for good daily variety!
"""
    )
