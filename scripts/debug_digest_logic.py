#!/usr/bin/env python3
"""
Отладочный скрипт для проверки логики формирования дайджеста.
Проверяет:
- Профиль пользователя (план, интересы, длина)
- Количество запрошенных атомов (max_atoms)
- Количество выбранных атомов из RAG
- Итоговый текст и количество абзацев
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.repo import session_scope
from app.models import User
from app.daily_digest_service import (
    build_daily_digest_for_user,
    make_user_profile_from_model,
    _compute_max_atoms,
)
from app.content_atoms_rag import select_atoms_for_day, select_general_day_atoms
from common.plans import get_user_plan


def debug_user_digest(user_id: int, day: date):
    """Отладка дайджеста для пользователя."""
    
    print(f"\n{'='*80}")
    print(f"DEBUG DIGEST FOR USER {user_id} on {day}")
    print(f"{'='*80}\n")
    
    with session_scope() as db:
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        # 1. План
        plan_code = get_user_plan(db, user_id)
        print(f"📊 PLAN: {plan_code}")
        
        # 2. Профиль
        profile = make_user_profile_from_model(user)
        print(f"🌍 LOCALE: {profile.locale}")
        print(f"🎯 INTERESTS: {profile.interests}")
        print(f"📏 PREFERRED_LENGTH: {profile.preferred_length}")
        
        # 3. Максимум атомов
        max_atoms = _compute_max_atoms(
            preferred_length=profile.preferred_length,
            plan_code=plan_code,
        )
        print(f"🔢 MAX_ATOMS (computed): {max_atoms}")
        
        # 4. Выбор атомов из RAG
        selected_atoms = select_atoms_for_day(
            db=db,
            user_id=user_id,
            day=day,
            user_profile=profile,
            max_total_atoms=max_atoms,
        )
        print(f"\n✅ SELECTED ATOMS: {len(selected_atoms)}")
        
        for i, sel in enumerate(selected_atoms, 1):
            atom = sel.atom
            print(f"\n  Atom #{i}:")
            print(f"    - ID: {atom.id}")
            print(f"    - trigger: {atom.trigger}")
            print(f"    - topic_tag: {atom.topic_tag}")
            print(f"    - persona_tags: {atom.persona_tags}")
            print(f"    - score: {sel.score:.2f}")
            print(f"    - body length: {len(atom.body) if atom.body else 0} chars")
            print(f"    - copy_short length: {len(atom.copy_short) if atom.copy_short else 0} chars")
            print(f"    - copy_long length: {len(atom.copy_long) if atom.copy_long else 0} chars")
            
            # Посчитаем абзацы в body
            if atom.body:
                paragraphs = [p.strip() for p in atom.body.split("\n\n") if p.strip()]
                print(f"    - paragraphs in body: {len(paragraphs)}")
        
        # 5. Итоговый дайджест
        print(f"\n{'='*80}")
        print("FINAL DIGEST TEXT")
        print(f"{'='*80}\n")
        
        digest = build_daily_digest_for_user(
            db=db,
            user=user,
            today=day,
            length=None,  # используем из профиля
        )
        
        print(f"📅 Date: {digest.date}")
        print(f"🌍 Locale: {digest.locale}")
        print(f"📏 Length: {digest.length}")
        print(f"📝 Title: {digest.title}")
        
        # Посчитаем, сколько атомов в итоге было использовано
        # (это можно сделать только косвенно по логам, но попробуем еще раз вызвать RAG)
        
        rag_atoms = select_atoms_for_day(
            db=db,
            user_id=user_id,
            day=day,
            user_profile=profile,
            max_total_atoms=max_atoms,
        )
        
        print(f"\n📊 ATOMS BREAKDOWN:")
        print(f"  - From RAG: {len(rag_atoms)}")
        
        total_atoms_used = rag_atoms[:]
        
        if len(rag_atoms) < max_atoms:
            remaining = max_atoms - len(rag_atoms)
            gen_atoms = select_general_day_atoms(
                db=db,
                user_profile=profile,
                max_atoms=remaining,
            )
            print(f"  - General day atoms added: {len(gen_atoms)}")
            total_atoms_used.extend(gen_atoms)
        
        print(f"  - TOTAL atoms used: {len(total_atoms_used)}")
        
        print(f"\n📖 Body ({len(digest.body)} chars):")
        print("-" * 80)
        
        # Посчитаем абзацы
        paragraphs = [p.strip() for p in digest.body.split("\n\n") if p.strip()]
        print(f"Total paragraphs: {len(paragraphs)}\n")
        
        for i, para in enumerate(paragraphs, 1):
            print(f"[{i}] {para[:100]}{'...' if len(para) > 100 else ''}")
        
        print("\n" + "-" * 80)
        print(f"\n💬 Affirmation: {digest.affirmation}")
        print(f"\n⚠️  Disclaimer: {digest.disclaimer[:80]}...")


def main():
    """Main entry point."""
    
    # Тестируем двух пользователей
    test_day = date(2026, 2, 16)
    
    user_ids = [2238, 2236]
    
    for user_id in user_ids:
        debug_user_digest(user_id, test_day)
        print("\n\n")


if __name__ == "__main__":
    main()
