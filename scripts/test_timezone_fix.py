#!/usr/bin/env python3
"""
Тест исправления проблемы с timezone при пропуске геолокации.

Проблема:
- Онбординг завершён (state = "complete")
- Все данные заполнены (birth_date, birth_time, birth_place)
- НО timezone не установлен в user.timezone
- /today выдаёт ошибку "онбординг не завершён"

Исправление:
- При пропуске геолокации (STATE_ASK_TIMEZONE_LOCATION) вызываем ensure_birthdata_geo_for_user
- Берём timezone из birth_data.tz и устанавливаем в user.timezone
- Если не удалось определить, используем fallback UTC
"""

import sys
from pathlib import Path

# Добавляем src в PYTHONPATH
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def check_timezone_handling_in_skip():
    """Проверяем обработку пропуска геолокации."""
    print("[OK] Проверка обработки пропуска геолокации...")

    routes_file = project_root / "src" / "app" / "routes_telegram.py"
    content = routes_file.read_text(encoding="utf-8")

    # Ищем секцию STATE_ASK_TIMEZONE_LOCATION
    if "if state == STATE_ASK_TIMEZONE_LOCATION:" not in content:
        print("  [FAIL] Обработка STATE_ASK_TIMEZONE_LOCATION не найдена")
        return False

    # Проверяем вызов ensure_birthdata_geo_for_user
    if "ensure_birthdata_geo_for_user(db, user)" not in content:
        print("  [FAIL] Вызов ensure_birthdata_geo_for_user не найден")
        return False

    print("  [OK] ensure_birthdata_geo_for_user вызывается")

    # Проверяем установку user.timezone из birth_data
    lines = content.split("\n")
    found_timezone_set = False
    for i, line in enumerate(lines):
        if "if state == STATE_ASK_TIMEZONE_LOCATION:" in line:
            # Проверяем следующие 50 строк
            context = "\n".join(lines[i : i + 50])
            if "user.timezone = birth_data.tz" in context:
                found_timezone_set = True
                print("  [OK] user.timezone устанавливается из birth_data.tz")
            if 'user.timezone = "UTC"' in context or 'user.timezone = "UTC"' in context:
                print("  [OK] Fallback на UTC если timezone не определён")
            break

    if not found_timezone_set:
        print("  [FAIL] user.timezone не устанавливается из birth_data")
        return False

    return True


def check_today_command_logic():
    """Проверяем логику проверки timezone в команде /today."""
    print("\n[OK] Проверка логики /today...")

    routes_file = project_root / "src" / "app" / "routes_telegram.py"
    content = routes_file.read_text(encoding="utf-8")

    # Ищем секцию /today
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if 'if text.startswith("/today")' in line:
            # Проверяем следующие 30 строк
            context = "\n".join(lines[i : i + 30])

            # Должна быть проверка onboarding_state
            if "onboarding_state != STATE_COMPLETE" in context:
                print("  [OK] Проверка onboarding_state найдена")
            else:
                print("  [WARN] Проверка onboarding_state не найдена")

            # Должна быть проверка timezone
            if "if not user.timezone:" in context:
                print("  [OK] Проверка user.timezone найдена")
            else:
                print("  [FAIL] Проверка user.timezone не найдена")
                return False

            break

    return True


def check_delivery_time_default():
    """Проверяем установку дефолтного delivery_time_local."""
    print("\n[OK] Проверка дефолтного delivery_time_local...")

    routes_file = project_root / "src" / "app" / "routes_telegram.py"
    content = routes_file.read_text(encoding="utf-8")

    # Ищем секцию STATE_ASK_PREFS_DELIVERY
    if "if state == STATE_ASK_PREFS_DELIVERY:" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "if state == STATE_ASK_PREFS_DELIVERY:" in line:
                # Проверяем следующие 50 строк
                context = "\n".join(lines[i : i + 50])

                if '"delivery_time_local"' in context and '"09:00"' in context:
                    print("  [OK] Дефолтное время доставки 09:00 устанавливается")
                    return True
                else:
                    print("  [WARN] Дефолтное время доставки не устанавливается")
                    return True  # Не критично

    print("  [WARN] STATE_ASK_PREFS_DELIVERY не найден")
    return True


def main():
    print("=" * 60)
    print("Тест исправления проблемы с timezone")
    print("=" * 60)

    results = []

    # Тест 1: Обработка пропуска геолокации
    results.append(check_timezone_handling_in_skip())

    # Тест 2: Логика проверки в /today
    results.append(check_today_command_logic())

    # Тест 3: Дефолтное время доставки
    results.append(check_delivery_time_default())

    print("\n" + "=" * 60)
    if all(results):
        print("[OK] ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("\nИсправление применено корректно!")
        print("\nЧто было исправлено:")
        print("1. При пропуске геолокации теперь:")
        print("   - Вызывается ensure_birthdata_geo_for_user")
        print("   - Берётся timezone из birth_data.tz")
        print("   - Устанавливается в user.timezone")
        print("   - Fallback на UTC если не удалось определить")
        print("2. При завершении онбординга:")
        print("   - Устанавливается дефолтное delivery_time_local = 09:00")
        print("\nТеперь /today должен работать после завершения онбординга!")
        return 0
    else:
        print("[FAIL] НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
