#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test that digests are now different for different users.
"""

from app.repo import session_scope
from app.daily_digest_service import build_daily_digest_for_user_id
from datetime import date

print("=" * 80)
print("TESTING PERSONALIZED DIGESTS")
print("=" * 80)
print()

test_users = {
    2238: {"name": "User 2238 (work, full plan, long)", "interests": "work"},
    2236: {"name": "User 2236 (money, daily plan, medium)", "interests": "money"},
}

digests = {}

with session_scope() as db:
    for user_id, info in test_users.items():
        print(f"{'=' * 80}")
        print(f"{info['name']}")
        print(f"{'=' * 80}")

        digest = build_daily_digest_for_user_id(db, user_id, today=date.today())

        if not digest:
            print(f"❌ Failed to generate digest for user {user_id}")
            continue

        digests[user_id] = digest

        print(f"Locale: {digest.locale}")
        print(f"Length setting: {digest.length}")
        print(f"Title: {digest.title}")
        print(f"Body length: {len(digest.body)} chars")
        print(f"Affirmation: {digest.affirmation[:60]}...")
        print()
        print("Body preview (first 300 chars):")
        print(digest.body[:300])
        print("...")
        print()

# Compare digests
print("=" * 80)
print("COMPARISON")
print("=" * 80)

if len(digests) == 2:
    d1 = digests[2238]
    d2 = digests[2236]

    print(f"\nLength difference:")
    print(f"  User 2238: {len(d1.body)} chars (length={d1.length})")
    print(f"  User 2236: {len(d2.body)} chars (length={d2.length})")
    print(f"  Difference: {abs(len(d1.body) - len(d2.body))} chars")

    print(f"\nTitle difference:")
    print(f"  User 2238: {d1.title}")
    print(f"  User 2236: {d2.title}")
    print(f"  Same title: {d1.title == d2.title}")

    print(f"\nBody similarity:")
    # Check if first 100 chars are the same
    same_start = d1.body[:100] == d2.body[:100]
    print(f"  First 100 chars identical: {same_start}")

    if d1.length != d2.length or d1.title != d2.title or not same_start:
        print("\n✅ SUCCESS: Digests are DIFFERENT (personalized!)")
    else:
        print("\n⚠️  WARNING: Digests are still very similar")

print("=" * 80)
