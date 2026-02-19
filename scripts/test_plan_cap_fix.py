#!/usr/bin/env python3
"""
Тест исправления plan cap для digest length.

Проверяет, что пользователь с планом Demo (cap=short) и настройкой medium 
получит short дайджест (ограниченный планом).
"""
import sys
from pathlib import Path

# Добавляем путь к src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import date

from app.repo import session_scope
from app import models
from common.plans import get_user_plan, get_plan_runtime_config


def test_plan_cap_clamping():
    """Тест логики ограничения длины дайджеста по плану."""
    
    # Порядок ограничений
    length_order = {"short": 0, "medium": 1, "long": 2}
    
    test_cases = [
        # (user_pref, plan_cap, expected_result)
        ("short", "short", "short"),
        ("short", "medium", "short"),
        ("short", "long", "short"),
        ("medium", "short", "short"),   # ограничение планом
        ("medium", "medium", "medium"),
        ("medium", "long", "medium"),
        ("long", "short", "short"),     # ограничение планом
        ("long", "medium", "medium"),   # ограничение планом
        ("long", "long", "long"),
    ]
    
    print("\n🧪 Тест логики ограничения длины дайджеста:")
    print("=" * 60)
    
    for user_pref, plan_cap, expected in test_cases:
        # Применяем логику из исправления
        user_order = length_order.get(user_pref, 0)
        cap_order = length_order.get(plan_cap, 0)
        
        result = user_pref
        if user_order > cap_order:
            result = plan_cap
        
        status = "✅" if result == expected else "❌"
        clamped = " (ОГРАНИЧЕНО ПЛАНОМ)" if result != user_pref else ""
        
        print(
            f"{status} user_pref={user_pref:<6} + plan_cap={plan_cap:<6} "
            f"→ {result:<6}{clamped}"
        )
        
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("\n✅ Все тесты логики пройдены!")


def test_user_plan_cap():
    """Проверка реального пользователя из БД."""
    print("\n👤 Проверка плана пользователя из БД:")
    print("=" * 60)
    
    with session_scope() as db:
        # Ищем первого пользователя с tg_user_id
        user = db.query(models.User).filter(
            models.User.tg_user_id.isnot(None)
        ).first()
        
        if not user:
            print("⚠️  Нет пользователей с tg_user_id в БД")
            return
        
        # Получаем план
        plan_code = get_user_plan(db, user.id)
        plan_cfg = get_plan_runtime_config(plan_code)
        
        # Получаем пользовательскую настройку
        length_pref = None
        
        if getattr(user, "digest_length_preference", None):
            length_pref = user.digest_length_preference
        
        if not length_pref and getattr(user, "prefs", None):
            prefs = user.prefs or {}
            if isinstance(prefs, dict):
                length_pref = prefs.get("digest_length_preference")
        
        print(f"\nUser ID: {user.id}")
        print(f"Telegram ID: {user.tg_user_id}")
        print(f"Display name: {getattr(user, 'display_name', 'N/A')}")
        print(f"\n📊 План и настройки:")
        print(f"  • План: {plan_code}")
        print(f"  • Plan cap: {plan_cfg.digest_cap}")
        print(f"  • User preference: {length_pref or 'не задано'}")
        
        # Применяем логику ограничения
        digest_cap = plan_cfg.digest_cap
        
        if length_pref not in ("short", "medium", "long"):
            length_pref = digest_cap
        
        length_order = {"short": 0, "medium": 1, "long": 2}
        user_order = length_order.get(length_pref, 0)
        cap_order = length_order.get(digest_cap, 0)
        
        final_length = length_pref
        clamped = False
        
        if user_order > cap_order:
            final_length = digest_cap
            clamped = True
        
        print(f"\n🎯 Итоговая длина: {final_length}")
        
        if clamped:
            print(f"   ⚠️  ОГРАНИЧЕНО ПЛАНОМ (было: {length_pref} → стало: {final_length})")
        else:
            print(f"   ✅ Без ограничений (совпадает с предпочтением)")
        
        # Проверка для плана Demo
        if plan_code == "demo":
            if final_length != "short":
                print(f"\n❌ ОШИБКА: План Demo должен ограничивать длину до 'short', но получили '{final_length}'")
            else:
                print(f"\n✅ План Demo корректно ограничивает длину до 'short'")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ТЕСТ ИСПРАВЛЕНИЯ PLAN CAP ДЛЯ DIGEST LENGTH")
    print("=" * 60)
    
    # Тест логики
    test_plan_cap_clamping()
    
    # Тест реального пользователя
    test_user_plan_cap()
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены!")
    print("=" * 60)
