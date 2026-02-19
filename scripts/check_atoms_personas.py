#!/usr/bin/env python3
"""
Проверка атомов в БД и их persona_tags.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.repo import session_scope
from app import models
from collections import defaultdict


def main():
    with session_scope() as db:
        atoms = (
            db.query(models.ContentAtom).filter(models.ContentAtom.locale == "ru").all()
        )

        print(f"Total RU atoms: {len(atoms)}\n")

        # Группируем по trigger
        by_trigger = defaultdict(list)
        for atom in atoms:
            trigger = atom.trigger or "NO_TRIGGER"
            by_trigger[trigger].append(atom)

        print("Atoms by trigger:")
        for trigger, atom_list in sorted(by_trigger.items()):
            print(f"\n  {trigger}: {len(atom_list)} atoms")
            for atom in atom_list:
                persona = atom.persona_tags or []
                print(f"    - ID={atom.id}, persona_tags={persona}")

        print("\n" + "=" * 80)
        print("Checking for work/money specific atoms:")
        print("=" * 80)

        work_atoms = [a for a in atoms if a.persona_tags and "work" in a.persona_tags]
        money_atoms = [a for a in atoms if a.persona_tags and "money" in a.persona_tags]

        print(f"\nAtoms with 'work' tag: {len(work_atoms)}")
        for atom in work_atoms[:5]:
            print(
                f"  - ID={atom.id}, trigger={atom.trigger}, persona={atom.persona_tags}"
            )

        print(f"\nAtoms with 'money' tag: {len(money_atoms)}")
        for atom in money_atoms[:5]:
            print(
                f"  - ID={atom.id}, trigger={atom.trigger}, persona={atom.persona_tags}"
            )


if __name__ == "__main__":
    main()
