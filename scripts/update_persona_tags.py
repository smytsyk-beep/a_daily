#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Russian atoms with persona_tags to enable personalization.

Persona tags mapping:
- work: работа, проекты, карьера
- relationships/love: отношения, люди
- money: деньги, финансы
- selfcare: забота о себе, энергия
"""

from app.repo import session_scope
from app import models

# Mapping: topic_tag -> persona_tags
PERSONA_TAGS_MAP = {
    # Transit atoms - обычно подходят для нескольких тем
    "tr_sun_moon_harmony": ["work", "selfcare"],  # гармония целей и эмоций
    "tr_mercury_venus_flow": ["work", "relationships"],  # коммуникация и договорённости
    "tr_mars_jupiter_drive": ["work", "money"],  # энергия и уверенность для действий
    "tr_mars_sun_push": ["work"],  # напряжение и энергия
    "tr_venus_mars_friction": ["relationships", "selfcare"],  # желания vs действия
    "tr_mercury_neptune_fog": [
        "work",
        "money",
    ],  # размытое мышление (важно для решений)
    "tr_sun_saturn_pressure": ["work", "selfcare"],  # ограничения и давление
    "tr_venus_jupiter_expansion": ["relationships", "money"],  # щедрость и удовольствия
    # Day general atoms - специфичные по теме
    "day_general_balance": ["selfcare"],
    "day_general_selfcare": ["selfcare"],
    "day_work_focus": ["work"],
    "day_money_focus": ["money"],
    "day_love_vibes": ["relationships"],
    "day_selfcare_nervous_system": ["selfcare"],
}

print("=" * 80)
print("UPDATING RUSSIAN ATOMS WITH PERSONA_TAGS")
print("=" * 80)
print()

with session_scope() as db:
    updated_count = 0

    ru_atoms = (
        db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
    )

    for atom in ru_atoms:
        topic_tag = atom.topic_tag

        if topic_tag in PERSONA_TAGS_MAP:
            new_tags = PERSONA_TAGS_MAP[topic_tag]
            old_tags = atom.persona_tags or []

            atom.persona_tags = new_tags

            print(f"✅ Atom {atom.id} ({topic_tag}):")
            print(f"   Old tags: {old_tags if old_tags else 'None'}")
            print(f"   New tags: {new_tags}")
            print()

            updated_count += 1
        else:
            print(f"⚠️  Atom {atom.id} ({topic_tag}): No mapping found, skipping")
            print()

    if updated_count > 0:
        print(f"Committing {updated_count} updates...")
        db.commit()
        print("✅ Done!")
    else:
        print("❌ No atoms updated")

    # Verify
    print()
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()

    ru_atoms = (
        db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
    )

    with_tags = sum(1 for a in ru_atoms if a.persona_tags and len(a.persona_tags) > 0)
    without_tags = len(ru_atoms) - with_tags

    print(f"Atoms with persona_tags: {with_tags}")
    print(f"Atoms without persona_tags: {without_tags}")

    if without_tags == 0:
        print("\n✅ SUCCESS: All Russian atoms now have persona_tags!")
    else:
        print(f"\n⚠️  WARNING: {without_tags} atoms still missing persona_tags")

print()
print("=" * 80)
