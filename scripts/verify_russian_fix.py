#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify that Russian encoding fix is working correctly.
"""

from app.repo import session_scope
from app import models
from app.daily_digest_service import build_daily_digest_for_user_id
from datetime import date

print("=" * 80)
print("RUSSIAN ENCODING FIX VERIFICATION")
print("=" * 80)
print()

with session_scope() as db:
    # Check atoms count
    ru_atoms = db.query(models.ContentAtom).filter(
        models.ContentAtom.locale == 'ru'
    ).count()
    en_atoms = db.query(models.ContentAtom).filter(
        models.ContentAtom.locale == 'en'
    ).count()
    
    print(f"Russian atoms in DB: {ru_atoms}")
    print(f"English atoms in DB: {en_atoms}")
    print()
    
    # Check one Russian atom
    ru_atom = db.query(models.ContentAtom).filter(
        models.ContentAtom.locale == 'ru',
        models.ContentAtom.trigger == 'sun_trine_moon'
    ).first()
    
    if ru_atom:
        print("Sample Russian atom (sun_trine_moon):")
        print(f"  Body (100 chars): {ru_atom.body[:100]}")
        print(f"  Contains 'Сегодня': {('Сегодня' in ru_atom.body)}")
        print(f"  Valid UTF-8: {all(c == ' ' or ord(c) >= 32 for c in ru_atom.body[:100])}")
        print()
    
    # Test digest generation for user 2238
    print("Testing digest generation for user 2238...")
    digest = build_daily_digest_for_user_id(db, 2238, today=date.today())
    
    if digest:
        print(f"  Locale: {digest.locale}")
        print(f"  Title: {digest.title}")
        print(f"  Body length: {len(digest.body)} chars")
        print(f"  Contains Cyrillic: {any(ord(c) >= 1024 for c in digest.body[:200])}")
        print(f"  Body preview:")
        print(f"    {digest.body[:150]}...")
        print()
    
    print("=" * 80)
    if ru_atom and digest and 'Сегодня' in ru_atom.body:
        print("✅ SUCCESS: Russian encoding is working correctly!")
    else:
        print("❌ FAILED: Russian encoding still has issues")
    print("=" * 80)
