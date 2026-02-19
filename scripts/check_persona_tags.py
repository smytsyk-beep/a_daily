#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check which atoms have persona_tags"""

from app.repo import session_scope
from app import models

with session_scope() as db:
    ru_atoms = (
        db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
    )

    print("=" * 80)
    print("RUSSIAN ATOMS PERSONA_TAGS CHECK")
    print("=" * 80)
    print()

    with_tags = 0
    without_tags = 0

    for atom in ru_atoms:
        tags = atom.persona_tags or []
        has_tags = len(tags) > 0

        if has_tags:
            with_tags += 1
            status = "✅"
        else:
            without_tags += 1
            status = "❌"

        print(f"{status} Atom {atom.id} ({atom.topic_tag}):")
        print(f"   Trigger: {atom.trigger}")
        print(f"   Persona tags: {tags if tags else 'NONE'}")
        print()

    print("=" * 80)
    print(f"Summary: {with_tags} atoms with persona_tags, {without_tags} without")
    print("=" * 80)

    if without_tags > 0:
        print(
            "\n⚠️  Problem: Atoms without persona_tags won't be matched to user interests!"
        )
        print("   This causes all users to get the same generic atoms.\n")
