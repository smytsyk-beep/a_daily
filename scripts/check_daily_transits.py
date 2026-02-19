#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if transits/events are calculated differently for 17.02 vs 18.02
"""

from app.repo import session_scope
from app import models
from app.astro_core import ensure_daily_transits
from app.daily_digest_service import (
    build_daily_digest_for_user_id,
    make_user_profile_from_model,
)
from app.content_atoms_rag import select_atoms_for_day
from datetime import date, timedelta

print("=" * 80)
print("CHECKING TRANSITS AND ATOMS FOR TWO DAYS")
print("=" * 80)
print()

user_id = 2238

# Two consecutive days
yesterday = date(2026, 2, 17)
today = date(2026, 2, 18)

with session_scope() as db:
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        print(f"❌ User {user_id} not found")
        exit(1)

    print(f"User {user_id}: locale={user.locale}, interests={user.prefs}")
    print()

    user_profile = make_user_profile_from_model(user)

    for day in [yesterday, today]:
        print("=" * 80)
        print(f"DATE: {day} ({'Yesterday' if day == yesterday else 'Today'})")
        print("=" * 80)
        print()

        # Ensure transits are calculated
        try:
            ensure_daily_transits(db, user_id, day)
        except Exception as e:
            print(f"⚠️  Error ensuring transits: {e}")

        # Get events for this user and day
        # Event model uses 'ts' (timestamp) field
        from datetime import datetime, timezone

        day_start = datetime.combine(day, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        day_end = datetime.combine(day, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )

        events = (
            db.query(models.Event)
            .filter(
                models.Event.user_id == user_id,
                models.Event.ts >= day_start,
                models.Event.ts <= day_end,
            )
            .all()
        )

        print(f"Events in database for {day}:")
        if events:
            for i, event in enumerate(events, 1):
                print(
                    f"  {i}. Event ID {event.id}: kind={event.kind}, title={event.title}"
                )
                if event.details:
                    trigger = event.details.get("trigger", "N/A")
                    transit_body = event.details.get("transit_body", "N/A")
                    natal_body = event.details.get("natal_body", "N/A")
                    aspect = event.details.get("aspect", "N/A")
                    print(
                        f"     Details: trigger={trigger}, {transit_body} {aspect} {natal_body}"
                    )
        else:
            print(f"  ❌ No events found for {day}")
        print()

        # Get selected atoms
        print(f"Atoms selected for {day}:")
        selected_atoms = select_atoms_for_day(
            db=db,
            user_id=user_id,
            day=day,
            user_profile=user_profile,
            max_total_atoms=6,
        )

        if selected_atoms:
            for i, sel in enumerate(selected_atoms, 1):
                atom = sel.atom
                print(
                    f"  {i}. Atom ID {atom.id}: {atom.trigger or 'no trigger'} | {atom.topic_tag} | score={sel.score:.2f}"
                )
                if sel.event:
                    print(f"     From event: {sel.event.kind}")
                if sel.transit:
                    print(f"     From transit: {sel.transit.kind}")
        else:
            print(f"  ❌ No atoms selected for {day}")
        print()

        # Generate digest
        print(f"Digest for {day}:")
        digest = build_daily_digest_for_user_id(db, user_id, today=day)

        if digest:
            print(f"  Title: {digest.title}")
            print(f"  Length: {len(digest.body)} chars")
            print(f"  First 150 chars: {digest.body[:150]}...")
        else:
            print(f"  ❌ Failed to generate digest")

        print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print(
    """
If events/atoms are the SAME for both days:
  → Problem: Transits not recalculating daily
  → Check: ensure_daily_transits, transit_service

If events/atoms are DIFFERENT but digest is the same:
  → Problem: Digest rendering or caching issue
  → Check: render logic, TODAY_CACHE key
"""
)
