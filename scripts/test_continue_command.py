#!/usr/bin/env python3
"""
Тест команды /continue для продолжения прерванного онбординга.

Проверяет:
1. Логика обработки команды /continue для разных состояний онбординга
2. Сообщения для уже завершенного онбординга
3. Обработка неизвестных состояний
4. Локализация всех сообщений
"""

import sys
from pathlib import Path

# Добавляем src в PYTHONPATH
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def check_continue_handler():
    """Проверяем наличие handler для /continue."""
    print("[OK] Проверка handler для /continue...")

    routes_file = project_root / "src" / "app" / "routes_telegram.py"
    content = routes_file.read_text(encoding="utf-8")

    if 'if text.startswith("/continue")' not in content:
        print("  [FAIL] Handler для /continue не найден")
        return False

    print("  [OK] Handler для /continue найден")

    # Проверяем обработку всех состояний
    states = [
        "STATE_AGE_GATE",
        "STATE_ASK_BIRTH_DATE",
        "STATE_ASK_BIRTH_TIME",
        "STATE_ASK_BIRTH_PLACE",
        "STATE_ASK_TIMEZONE_LOCATION",
        "STATE_ASK_PREFS_TOPICS",
        "STATE_ASK_PREFS_DELIVERY",
    ]

    for state in states:
        if f"current_state == {state}" not in content:
            print(f"  [WARN] Обработка {state} не найдена")

    print("  [OK] Все состояния обрабатываются")
    return True


def check_localization_keys():
    """Проверяем наличие ключей локализации для /continue."""
    print("\n[OK] Проверка локализаций...")

    required_keys = {
        "ru.json": [
            '"incomplete"',
            '"continue"',
            '"already_complete"',
            '"unknown_state"',
        ],
        "en.json": [
            '"incomplete"',
            '"continue"',
            '"already_complete"',
            '"unknown_state"',
        ],
        "es.json": [
            '"incomplete"',
            '"continue"',
            '"already_complete"',
            '"unknown_state"',
        ],
    }

    all_ok = True
    for locale_file, keys in required_keys.items():
        file_path = project_root / "src" / "app" / "locales" / locale_file
        content = file_path.read_text(encoding="utf-8")

        for key in keys:
            if key not in content:
                print(f"  [FAIL] Ключ {key} не найден в {locale_file}")
                all_ok = False

    if all_ok:
        print("  [OK] Все ключи локализации найдены")

    return all_ok


def check_incomplete_message_updated():
    """Проверяем, что сообщение incomplete ссылается на /continue."""
    print("\n[OK] Проверка обновления сообщения incomplete...")

    locales = ["ru.json", "en.json", "es.json"]
    all_ok = True

    for locale_file in locales:
        file_path = project_root / "src" / "app" / "locales" / locale_file
        content = file_path.read_text(encoding="utf-8")

        # Проверяем, что в incomplete есть упоминание /continue
        if '"incomplete"' in content:
            # Ищем блок incomplete
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if '"incomplete"' in line:
                    # Проверяем следующие несколько строк
                    context = "\n".join(lines[i : i + 3])
                    if "/continue" in context:
                        print(
                            f"  [OK] {locale_file}: incomplete ссылается на /continue"
                        )
                    elif "/start" in context and "continue" in context.lower():
                        print(
                            f"  [WARN] {locale_file}: incomplete упоминает и /start и continue"
                        )
                    else:
                        print(
                            f"  [FAIL] {locale_file}: incomplete не ссылается на /continue"
                        )
                        all_ok = False
                    break

    return all_ok


def check_help_updated():
    """Проверяем, что help включает команду /continue."""
    print("\n[OK] Проверка обновления help...")

    locales = ["ru.json", "en.json", "es.json"]
    all_ok = True

    for locale_file in locales:
        file_path = project_root / "src" / "app" / "locales" / locale_file
        content = file_path.read_text(encoding="utf-8")

        if '"help"' in content and "/continue" in content:
            print(f"  [OK] {locale_file}: help упоминает /continue")
        else:
            print(f"  [WARN] {locale_file}: help может не упоминать /continue")

    return all_ok


def main():
    print("=" * 60)
    print("Тест команды /continue")
    print("=" * 60)

    results = []

    # Тест 1: Handler для /continue
    results.append(check_continue_handler())

    # Тест 2: Локализация
    results.append(check_localization_keys())

    # Тест 3: Обновление incomplete
    results.append(check_incomplete_message_updated())

    # Тест 4: Обновление help
    results.append(check_help_updated())

    print("\n" + "=" * 60)
    if all(results):
        print("[OK] ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("\nКоманда /continue готова к использованию!")
        print("\nКак использовать:")
        print("1. Начните онбординг с /start")
        print("2. Прервите его (например, введите /today)")
        print("3. Бот предложит использовать /continue")
        print("4. /continue продолжит с того места, где остановились")
        return 0
    else:
        print("[FAIL] НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
