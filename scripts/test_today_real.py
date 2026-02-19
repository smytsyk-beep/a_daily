#!/usr/bin/env python3
"""
Тестируем реальный вызов /today для двух пользователей.
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.repo import session_scope
from app.modules.daily_digest import compute


def test_today_for_user(user_id: int):
    """Эмулирует вызов /today для пользователя."""

    print(f"\n{'='*80}")
    print(f"TEST /today FOR USER {user_id}")
    print(f"{'='*80}\n")

    try:
        # compute() возвращает List[Atom], где первый атом — это дайджест
        atoms = compute(user_id=user_id, config=None)

        if not atoms:
            print("❌ No atoms returned")
            return

        digest_atom = atoms[0]

        print(f"📊 Module: {digest_atom.get('module')}")
        print(f"📝 Title: {digest_atom.get('title')}")
        print(f"🌍 Locale: {digest_atom.get('locale')}")
        print(f"📏 Length: {digest_atom.get('length')}")
        print(f"📅 Date: {digest_atom.get('date')}")

        body = digest_atom.get("body", "")

        # Посчитаем абзацы
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        print(f"\n📖 Body ({len(body)} chars, {len(paragraphs)} paragraphs):")
        print("-" * 80)

        for i, para in enumerate(paragraphs, 1):
            print(f"[{i}] {para[:120]}{'...' if len(para) > 120 else ''}")

        print("\n" + "-" * 80)
        print(f"\n💬 Affirmation: {digest_atom.get('affirmation', '')[:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main entry point."""

    user_ids = [2238, 2236]

    for user_id in user_ids:
        test_today_for_user(user_id)
        print("\n\n")


if __name__ == "__main__":
    main()
