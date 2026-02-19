#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики выбора атомов с разными планами и длиной дайджеста.

Usage:
    python scripts/test_atom_selection_logic.py --user-id 1888
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import logging
from datetime import date

from app.repo import session_scope
from app import models
from app.daily_digest_service import build_daily_digest_for_user
from common.plans import get_user_plan

# Включаем подробное логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def test_user_digest(user_id: int, test_date: date | None = None):
    """Тестирует построение дайджеста для пользователя."""
    if test_date is None:
        test_date = date.today()

    print(f"\n{'=' * 80}")
    print(f"Testing digest generation for user_id={user_id} on date={test_date}")
    print(f"{'=' * 80}\n")

    with session_scope() as db:
        # 1. Загружаем пользователя
        user = db.query(models.User).filter(models.User.id == user_id).one_or_none()
        if not user:
            print(f"❌ User {user_id} NOT FOUND")
            return

        print(f"✅ User found:")
        print(f"   - id: {user.id}")
        print(f"   - tg_user_id: {user.tg_user_id}")
        print(f"   - locale: {user.locale}")
        print(f"   - digest_interests: {getattr(user, 'digest_interests', None)}")
        print(
            f"   - digest_length_preference: {getattr(user, 'digest_length_preference', None)}"
        )
        print()

        # 2. План пользователя
        plan_code = get_user_plan(db, user.id)
        print(f"📋 User plan: {plan_code}")
        print()

        # 3. Строим дайджест (без override длины)
        print(f"🔄 Building digest with user's default settings...")
        print()
        
        digest = build_daily_digest_for_user(db=db, user=user, today=test_date)

        print(f"\n{'=' * 80}")
        print(f"RESULT:")
        print(f"{'=' * 80}")
        print(f"Title: {digest.title}")
        print(f"Length: {digest.length}")
        print(f"Body length: {len(digest.body)} chars")
        print(f"Paragraphs: {len(digest.body.split(chr(10) + chr(10)))}")
        print()
        print("Body:")
        print("-" * 80)
        print(digest.body)
        print("-" * 80)
        print()
        print(f"Affirmation: {digest.affirmation}")
        print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test atom selection logic for different plans and digest lengths"
    )
    parser.add_argument(
        "--user-id", type=int, required=True, help="User ID to test"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to test (YYYY-MM-DD), default: today",
    )

    args = parser.parse_args()

    test_date = None
    if args.date:
        test_date = date.fromisoformat(args.date)

    test_user_digest(args.user_id, test_date)


if __name__ == "__main__":
    main()
