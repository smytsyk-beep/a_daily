#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test digest for 18.02 after adding new atoms"""

from app.repo import session_scope
from app.daily_digest_service import build_daily_digest_for_user_id
from datetime import date

user_id = 2238
today = date(2026, 2, 18)

print("=" * 80)
print(f"TESTING DIGEST FOR USER {user_id} ON {today}")
print("=" * 80)
print()

with session_scope() as db:
    digest = build_daily_digest_for_user_id(db, user_id, today=today)

    if digest:
        print(f"Title: {digest.title}")
        print(f"Length: {len(digest.body)} chars")
        print()
        print("Body:")
        print(digest.body)
        print()
        print(f"Affirmation: {digest.affirmation}")
    else:
        print("❌ Failed to generate digest")

print()
print("=" * 80)
