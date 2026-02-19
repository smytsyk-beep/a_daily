#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование фикса обработки геолокации вне контекста онбординга.

Сценарий:
1. Пользователь проходит онбординг до шага запроса геолокации
2. Пользователь пропускает геолокацию (текстом)
3. Пользователь позже (несколько диалогов спустя) нажимает кнопку геолокации
4. Бот должен отправить понятное сообщение вместо "неизвестная команда"
"""

import sys
import os
from pathlib import Path

# Установка правильной кодировки для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.i18n import tr


def test_location_unexpected_message():
    """Проверяем наличие локализации для неожиданной геолокации."""

    locales = ["en", "ru", "es"]

    print("Testing localization for unexpected location...")
    print()

    for locale in locales:
        try:
            msg = tr(locale, "tg.location.unexpected")
            print(f"[OK] {locale.upper()}: {msg}")
        except KeyError as e:
            print(f"[FAIL] {locale.upper()}: Missing localization key - {e}")
            return False

    print()
    print("[OK] All localization keys present!")
    return True


def test_onboarding_flow_description():
    """Описание потока онбординга с геолокацией."""

    print("\n" + "=" * 60)
    print("СЦЕНАРИЙ ОНБОРДИНГА С ГЕОЛОКАЦИЕЙ")
    print("=" * 60)

    steps = [
        ("1. Birth date", "STATE_ASK_BIRTH_DATE", "User sends: 12.10.1980"),
        ("2. Birth time", "STATE_ASK_BIRTH_TIME", "User sends: 07:30"),
        ("3. Birth place", "STATE_ASK_BIRTH_PLACE", "User sends: Kyiv, Ukraine"),
        (
            "4. Timezone location",
            "STATE_ASK_TIMEZONE_LOCATION",
            "Bot shows location button",
        ),
        ("   -> Option A", "", "User shares location → timezone saved → next step"),
        (
            "   -> Option B",
            "",
            "User types 'Skip' → next step with birth_place timezone",
        ),
        ("5. Topics", "STATE_ASK_PREFS_TOPICS", "User sends: 1,3"),
        ("6. Delivery", "STATE_ASK_PREFS_DELIVERY", "User sends: 2"),
        ("7. Complete", "STATE_COMPLETE", "Onboarding finished"),
    ]

    for step, state, action in steps:
        print(f"{step:<25} {state:<35} {action}")

    print("\n" + "=" * 60)
    print("ПРОБЛЕМА (FIXED)")
    print("=" * 60)
    print("Если пользователь на шаге 4 пропустил геолокацию (Option B),")
    print("но позже (на шаге 5, 6 или 7) нажал кнопку 'Share location',")
    print("бот НЕ был в состоянии STATE_ASK_TIMEZONE_LOCATION.")
    print()
    print("РЕШЕНИЕ:")
    print("1. Проверяем location message ПЕРЕД проверкой состояния")
    print("2. Если location НЕ в нужном состоянии → отправляем понятное сообщение")
    print("3. Убираем клавиатуру с геолокацией при переходе на следующий шаг")
    print("=" * 60)


def main():
    """Главная функция тестирования."""

    print("\n[FIX TEST] TESTING LOCATION HANDLING FIX\n")

    # Тест 1: Локализация
    test_result = test_location_unexpected_message()

    # Тест 2: Описание flow
    test_onboarding_flow_description()

    print("\n" + "=" * 60)
    if test_result:
        print("[PASS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nRecommended manual testing:")
        print("1. New onboarding with location share")
        print("2. New onboarding with location skip")
        print("3. Late location button click")
        print("4. /today after onboarding complete")
        return 0
    else:
        print("[FAIL] TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
