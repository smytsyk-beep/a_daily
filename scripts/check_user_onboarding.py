#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки данных пользователя после онбординга.
"""

import sys
import os
from pathlib import Path

# Установка правильной кодировки для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.repo import session_scope
from app import models, repo
from sqlalchemy import select


def check_user_by_tg_id(tg_user_id: int):
    """Проверяет данные пользователя по Telegram ID."""
    
    with session_scope() as db:
        stmt = select(models.User).where(models.User.tg_user_id == tg_user_id)
        user = db.execute(stmt).scalar_one_or_none()
        
        if not user:
            print(f"[ERROR] User with tg_user_id={tg_user_id} not found")
            return False
        
        print(f"\n{'='*60}")
        print(f"USER DATA FOR tg_user_id={tg_user_id}")
        print(f"{'='*60}\n")
        
        # Основные данные
        print(f"Internal ID: {user.id}")
        print(f"Username: {user.username or 'N/A'}")
        print(f"Locale: {user.locale}")
        print(f"Timezone: {user.timezone or 'NOT SET'}")
        print(f"Delivery enabled: {user.delivery_enabled}")
        print(f"Delivery time local: {user.delivery_time_local or 'NOT SET'}")
        print(f"Digest length pref: {user.digest_length_preference or 'NOT SET'}")
        
        # Prefs (JSONB)
        print(f"\n--- PREFS (JSONB) ---")
        prefs = user.prefs or {}
        if isinstance(prefs, dict):
            for key, value in prefs.items():
                print(f"  {key}: {value}")
        else:
            print(f"  (not a dict: {type(prefs)})")
        
        # Birth data
        print(f"\n--- BIRTH DATA ---")
        bd_stmt = select(models.BirthData).where(models.BirthData.user_ref == str(user.id))
        bd = db.execute(bd_stmt).scalar_one_or_none()
        
        if bd:
            print(f"  Birth date: {bd.birth_date}")
            print(f"  Birth time: {bd.birth_time}")
            print(f"  Place: {bd.place}")
            print(f"  Lat/Lon: {bd.lat}, {bd.lon}")
            print(f"  Timezone (BD): {bd.tz}")
        else:
            print(f"  [ERROR] No BirthData found for user_ref={user.id}")
        
        # Onboarding state
        onboarding_state = prefs.get("onboarding_state") if isinstance(prefs, dict) else None
        print(f"\n--- ONBOARDING ---")
        print(f"  State: {onboarding_state or 'COMPLETE'}")
        
        # Проверка готовности для /today
        print(f"\n--- READINESS FOR /today ---")
        issues = []
        
        if not user.timezone:
            issues.append("❌ timezone not set")
        else:
            print(f"  ✅ timezone: {user.timezone}")
        
        if not bd:
            issues.append("❌ birth_data missing")
        elif not bd.lat or not bd.lon:
            issues.append("❌ birth_data missing lat/lon")
        else:
            print(f"  ✅ birth_data: OK")
        
        if onboarding_state and onboarding_state != "complete":
            issues.append(f"❌ onboarding not complete: {onboarding_state}")
        else:
            print(f"  ✅ onboarding: complete")
        
        if issues:
            print(f"\n[WARNING] Issues found:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print(f"\n[SUCCESS] User is ready for /today!")
            return True


def main():
    """Главная функция."""
    
    if len(sys.argv) < 2:
        print("Usage: python check_user_data.py <telegram_user_id>")
        print("Example: python check_user_data.py 123456789")
        return 1
    
    try:
        tg_user_id = int(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid telegram_user_id: {sys.argv[1]}")
        return 1
    
    success = check_user_by_tg_id(tg_user_id)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
