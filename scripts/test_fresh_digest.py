#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate fresh digest and verify encoding"""

from app.repo import session_scope
from app.daily_digest_service import build_daily_digest_for_user_id
from datetime import date

print("=" * 80)
print("GENERATING FRESH DIGEST FOR USER 2238")
print("=" * 80)
print()

with session_scope() as db:
    digest = build_daily_digest_for_user_id(db, 2238, today=date.today())
    
    if not digest:
        print("❌ Failed to generate digest")
        exit(1)
    
    print(f"Locale: {digest.locale}")
    print(f"Length: {digest.length}")
    print(f"Title: {digest.title}")
    print()
    print("=" * 80)
    print("DIGEST BODY:")
    print("=" * 80)
    print(digest.body)
    print()
    print("=" * 80)
    print("AFFIRMATION:")
    print("=" * 80)
    print(digest.affirmation if digest.affirmation else "None")
    print()
    
    # Check encoding
    has_cyrillic = any(ord(c) >= 1024 for c in digest.body)
    has_questions = digest.body.count('?') > len(digest.body) * 0.1
    
    print("=" * 80)
    print("ENCODING CHECK:")
    print("=" * 80)
    print(f"Contains Cyrillic characters: {has_cyrillic}")
    print(f"Has suspicious question marks: {has_questions}")
    
    if has_cyrillic and not has_questions:
        print("\n✅ SUCCESS: Digest has correct Russian encoding!")
    else:
        print("\n❌ WARNING: Digest may have encoding issues")
        print(f"   Cyrillic: {has_cyrillic}, Questions: {has_questions}")
    
    print("=" * 80)
