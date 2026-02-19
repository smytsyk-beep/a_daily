#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose why users get identical digests despite different settings.
"""

from app.repo import session_scope
from app import models
from app.daily_digest_service import (
    build_daily_digest_for_user_id,
    make_user_profile_from_model,
)
from app.content_atoms_rag import select_atoms_for_day
from datetime import date
from common.plans import get_user_plan, get_plan_config

print("=" * 80)
print("DIAGNOSING IDENTICAL DIGESTS ISSUE")
print("=" * 80)
print()

test_users = [2238, 2236]

with session_scope() as db:
    for user_id in test_users:
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            print(f"❌ User {user_id} not found")
            continue

        print(f"{'=' * 80}")
        print(f"USER {user_id}")
        print(f"{'=' * 80}")

        # User settings
        print(f"Locale: {user.locale}")
        print(f"Timezone: {user.timezone}")

        # Plan
        plan_code = get_user_plan(db, user_id)
        plan_config = get_plan_config(plan_code)
        print(f"Plan: {plan_code} (digest_cap: {plan_config.digest_cap})")

        # Interests
        prefs = getattr(user, "prefs", None) or {}
        interests = (
            prefs.get("focus_topics")
            or prefs.get("digest_interests")
            or getattr(user, "digest_interests", None)
            or ["general"]
        )
        print(f"Interests: {interests}")

        # Digest length preference
        length_pref = (
            prefs.get("text_length")
            or prefs.get("digest_length_preference")
            or getattr(user, "digest_length_preference", None)
            or "medium"
        )
        print(f"Length preference: {length_pref}")

        # User profile for atom selection
        user_profile = make_user_profile_from_model(user)
        print(f"\nUserProfile:")
        print(f"  locale: {user_profile.locale}")
        print(f"  interests: {user_profile.interests}")
        print(f"  preferred_length: {user_profile.preferred_length}")

        # Get selected atoms for today
        print(f"\nAtoms selected for today ({date.today()}):")
        selected_atoms = select_atoms_for_day(
            db=db,
            user_id=user.id,
            day=date.today(),
            user_profile=user_profile,
            max_total_atoms=6,
        )

        print(f"  Total atoms selected: {len(selected_atoms)}")
        for i, sel in enumerate(selected_atoms, 1):
            atom = sel.atom
            print(
                f"  {i}. Atom ID {atom.id}: {atom.trigger or 'no trigger'} | {atom.topic_tag} | score={sel.score:.2f}"
            )
            if sel.transit:
                print(f"     Transit: {sel.transit.kind}")
            if sel.event:
                print(f"     Event: {sel.event.kind}")

        print()

print("=" * 80)
print("CHECKING ATOM VARIETY")
print("=" * 80)

with session_scope() as db:
    # Check total Russian atoms
    ru_atoms = (
        db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
    )

    print(f"\nTotal Russian atoms: {len(ru_atoms)}")

    # Count by trigger
    by_trigger = {}
    for atom in ru_atoms:
        trigger = atom.trigger or "no_trigger"
        by_trigger[trigger] = by_trigger.get(trigger, 0) + 1

    print("\nAtoms by trigger:")
    for trigger, count in sorted(by_trigger.items()):
        print(f"  {trigger}: {count} atoms")

    # Count by topic_tag
    by_topic = {}
    for atom in ru_atoms:
        topic = atom.topic_tag or "no_topic"
        by_topic[topic] = by_topic.get(topic, 0) + 1

    print("\nAtoms by topic_tag:")
    for topic, count in sorted(by_topic.items()):
        print(f"  {topic}: {count} atoms")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print(
    """
Possible causes for identical digests:
1. Not enough atom variety (only 16 Russian atoms vs 399 English)
2. Atom selection doesn't consider user interests (persona_tags)
3. Same transits/events for both users
4. Cache key collision (unlikely if user_id is in key)
"""
)
