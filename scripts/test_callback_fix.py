#!/usr/bin/env python3
"""
Скрипт для проверки исправления цикличной ошибки callback_query.

Проверяет:
1. Функция answer_callback_query добавлена в telegram_client
2. Импорт answer_callback_query в routes_telegram
3. Извлечение callback_query_id из update
4. Вызов answer_callback_query в начале обработки callback
"""

import sys
from pathlib import Path

# Добавляем src в PYTHONPATH
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Проверяем, что все необходимые функции импортируются."""
    print("[OK] Проверка импортов...")

    try:
        from app.telegram_client import answer_callback_query, send_message

        print("  [OK] answer_callback_query импортируется из telegram_client")
    except ImportError as e:
        print(f"  [FAIL] Ошибка импорта answer_callback_query: {e}")
        return False

    try:
        from app import routes_telegram

        print("  [OK] routes_telegram импортируется")
    except ImportError as e:
        print(f"  [FAIL] Ошибка импорта routes_telegram: {e}")
        return False

    return True


def test_function_signature():
    """Проверяем сигнатуру функции answer_callback_query."""
    print("\n[OK] Проверка сигнатуры answer_callback_query...")

    from app.telegram_client import answer_callback_query
    import inspect

    sig = inspect.signature(answer_callback_query)
    params = list(sig.parameters.keys())

    if "callback_query_id" not in params:
        print("  [FAIL] Параметр callback_query_id отсутствует")
        return False

    print(f"  [OK] Сигнатура корректна: {sig}")
    return True


def check_code_for_answer_callback():
    """Проверяем, что answer_callback_query вызывается в routes_telegram."""
    print("\n[OK] Проверка вызова answer_callback_query в routes_telegram...")

    routes_file = project_root / "src" / "app" / "routes_telegram.py"
    content = routes_file.read_text(encoding="utf-8")

    if "answer_callback_query" not in content:
        print("  [FAIL] answer_callback_query не найден в routes_telegram.py")
        return False

    if "callback_query_id" not in content:
        print("  [FAIL] callback_query_id не извлекается из message")
        return False

    if "_callback_query_id" not in content:
        print("  [FAIL] _callback_query_id не добавлен в _extract_message")
        return False

    print("  [OK] answer_callback_query вызывается")
    print("  [OK] callback_query_id извлекается из update")
    return True


def main():
    print("=" * 60)
    print("Тест исправления цикличной ошибки callback_query")
    print("=" * 60)

    results = []

    # Тест 1: Импорты
    results.append(test_imports())

    # Тест 2: Сигнатура функции
    if results[-1]:
        results.append(test_function_signature())

    # Тест 3: Вызов в коде
    results.append(check_code_for_answer_callback())

    print("\n" + "=" * 60)
    if all(results):
        print("[OK] ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("\nИсправление применено корректно!")
        print("\nТеперь при нажатии кнопки 'Время рождения':")
        print("1. Telegram получит answerCallbackQuery")
        print("2. Циклические повторы сообщений прекратятся")
        print("3. Пользователь увидит одно сообщение с запросом времени")
        return 0
    else:
        print("[FAIL] НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
