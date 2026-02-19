#!/usr/bin/env python3
"""
Тестирование логики выбора атомов для конкретных пользователей.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
from datetime import date

from app.repo import session_scope
from app import models
from app.daily_digest_service import build_daily_digest_for_user, make_user_profile_from_model, _compute_max_atoms
from common.plans import get_user_plan

# Включаем ОЧЕНЬ подробное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s | %(levelname)s | %(message)s",
)


def compare_users(user_id_1: int, user_id_2: int):
    """Сравнивает дайджесты двух пользователей."""
    
    print(f"\n{'='*100}")
    print(f"COMPARING DIGESTS FOR user_id={user_id_1} vs user_id={user_id_2}")
    print(f"{'='*100}\n")
    
    with session_scope() as db:
        # Пользователь 1
        user1 = db.query(models.User).filter(models.User.id == user_id_1).one_or_none()
        if not user1:
            print(f"❌ User {user_id_1} NOT FOUND")
            return
        
        # Пользователь 2
        user2 = db.query(models.User).filter(models.User.id == user_id_2).one_or_none()
        if not user2:
            print(f"❌ User {user_id_2} NOT FOUND")
            return
        
        print("USER 1:")
        print(f"  ID: {user1.id}")
        print(f"  Locale: {user1.locale}")
        print(f"  Interests: {user1.digest_interests}")
        print(f"  Length pref: {user1.digest_length_preference}")
        
        profile1 = make_user_profile_from_model(user1)
        plan1 = get_user_plan(db, user1.id)
        max_atoms1 = _compute_max_atoms(profile1.preferred_length, plan1)
        
        print(f"  Profile interests: {profile1.interests}")
        print(f"  Profile length: {profile1.preferred_length}")
        print(f"  Plan: {plan1}")
        print(f"  Max atoms: {max_atoms1}")
        
        print("\nUSER 2:")
        print(f"  ID: {user2.id}")
        print(f"  Locale: {user2.locale}")
        print(f"  Interests: {user2.digest_interests}")
        print(f"  Length pref: {user2.digest_length_preference}")
        
        profile2 = make_user_profile_from_model(user2)
        plan2 = get_user_plan(db, user2.id)
        max_atoms2 = _compute_max_atoms(profile2.preferred_length, plan2)
        
        print(f"  Profile interests: {profile2.interests}")
        print(f"  Profile length: {profile2.preferred_length}")
        print(f"  Plan: {plan2}")
        print(f"  Max atoms: {max_atoms2}")
        
        print(f"\n{'='*100}")
        print("BUILDING DIGEST FOR USER 1")
        print(f"{'='*100}\n")
        
        digest1 = build_daily_digest_for_user(db=db, user=user1, today=date.today())
        
        print(f"\n{'='*100}")
        print("BUILDING DIGEST FOR USER 2")
        print(f"{'='*100}\n")
        
        digest2 = build_daily_digest_for_user(db=db, user=user2, today=date.today())
        
        print(f"\n{'='*100}")
        print("COMPARISON RESULTS")
        print(f"{'='*100}\n")
        
        print(f"User 1 digest length: {digest1.length} ({len(digest1.body)} chars, {len(digest1.body.split(chr(10)+chr(10)))} paragraphs)")
        print(f"User 2 digest length: {digest2.length} ({len(digest2.body)} chars, {len(digest2.body.split(chr(10)+chr(10)))} paragraphs)")
        
        print(f"\nDigests are {'IDENTICAL' if digest1.body == digest2.body else 'DIFFERENT'}")
        
        if digest1.body == digest2.body:
            print("\n⚠️  PROBLEM: Digests are identical despite different settings!")
            print("\nUser 1 body preview:")
            print(digest1.body[:200] + "...")
            print("\nUser 2 body preview:")
            print(digest2.body[:200] + "...")


if __name__ == "__main__":
    # ID из скриншотов
    # User 1: Plan=Full, Length=long, Interests=money+selfcare
    # User 2: Plan=Daily, Length=medium, Interests=selfcare
    user_id_1 = int(sys.argv[1]) if len(sys.argv) > 1 else 1888
    user_id_2 = int(sys.argv[2]) if len(sys.argv) > 2 else 1889
    
    compare_users(user_id_1, user_id_2)
