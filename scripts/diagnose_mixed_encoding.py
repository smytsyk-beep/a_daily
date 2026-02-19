#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose why digest has mixed encoding"""

from app.repo import session_scope
from app import models
from app.daily_digest_service import (
    build_daily_digest_for_user,
    make_user_profile_from_model,
)
from app.content_atoms_rag import select_atoms_for_day
from datetime import date

print("=" * 80)
print("DIAGNOSING MIXED ENCODING IN DIGEST")
print("=" * 80)
print()

with session_scope() as db:
    # Get user
    user = db.query(models.User).filter(models.User.id == 2238).first()

    if not user:
        print("User 2238 not found")
        exit(1)

    print(f"User locale: {user.locale}")
    print()

    # Check all Russian atoms
    print("Checking ALL Russian atoms in database:")
    print("-" * 80)

    all_ru_atoms = (
        db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
    )

    broken_count = 0
    good_count = 0

    for atom in all_ru_atoms:
        has_cyrillic = "Сегодня" in atom.body or any(
            ord(c) >= 1024 for c in atom.body[:50]
        )
        has_questions = atom.body.count("?") > len(atom.body) * 0.3

        if has_questions and not has_cyrillic:
            broken_count += 1
            print(
                f"❌ BROKEN: ID={atom.id}, trigger={atom.trigger}, topic={atom.topic_tag}"
            )
            print(f"   Body: {atom.body[:80]}...")
        else:
            good_count += 1
            if good_count <= 3:  # Show first 3 good ones
                print(
                    f"✅ GOOD: ID={atom.id}, trigger={atom.trigger}, topic={atom.topic_tag}"
                )
                print(f"   Body: {atom.body[:80]}...")

    print()
    print(f"Summary: {good_count} good atoms, {broken_count} broken atoms")
    print()

    # Now check which atoms are being selected for digest
    print("=" * 80)
    print("Atoms selected for today's digest:")
    print("-" * 80)

    user_profile = make_user_profile_from_model(user)
    selected = select_atoms_for_day(
        db=db,
        user_id=user.id,
        day=date.today(),
        user_profile=user_profile,
        max_total_atoms=6,
    )

    for i, sel in enumerate(selected, 1):
        atom = sel.atom
        has_cyrillic = (
            any(ord(c) >= 1024 for c in atom.body[:50]) if atom.body else False
        )
        has_questions = (
            atom.body.count("?") > len(atom.body) * 0.3 if atom.body else False
        )
        status = "✅ GOOD" if has_cyrillic and not has_questions else "❌ BROKEN"

        print(f"\n{i}. {status} - Atom ID {atom.id}")
        print(f"   Trigger: {atom.trigger}")
        print(f"   Topic: {atom.topic_tag}")
        print(f"   Body preview: {atom.body[:100] if atom.body else 'None'}...")

        if atom.copy_long:
            has_cyrillic_long = any(ord(c) >= 1024 for c in atom.copy_long[:50])
            has_questions_long = atom.copy_long.count("?") > len(atom.copy_long) * 0.3
            status_long = "✅" if has_cyrillic_long and not has_questions_long else "❌"
            print(f"   Copy long {status_long}: {atom.copy_long[:100]}...")

    print()
    print("=" * 80)
