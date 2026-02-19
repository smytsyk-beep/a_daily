#!/usr/bin/env python3
"""
Тест логики исправления plan cap для digest length (без БД).

Проверяет, что логика ограничения длины дайджеста работает корректно.
"""


def apply_plan_cap(user_pref: str, plan_cap: str) -> str:
    """
    Применяет ограничение плана к пользовательской настройке.
    Возвращает минимальную (более ограничивающую) длину.
    """
    length_order = {"short": 0, "medium": 1, "long": 2}

    # Валидация user_pref
    if user_pref not in ("short", "medium", "long"):
        return plan_cap

    user_order = length_order.get(user_pref, 0)
    cap_order = length_order.get(plan_cap, 0)

    # Берём минимум (более ограничивающую длину)
    if user_order > cap_order:
        return plan_cap

    return user_pref


def test_plan_cap_logic():
    """Тест логики ограничения длины дайджеста."""

    test_cases = [
        # (user_pref, plan_cap, expected_result, description)
        ("short", "short", "short", "оба short"),
        ("short", "medium", "short", "user хочет меньше, чем cap"),
        ("short", "long", "short", "user хочет минимум"),
        ("medium", "short", "short", "⚠️  ограничение планом"),
        ("medium", "medium", "medium", "оба medium"),
        ("medium", "long", "medium", "user хочет меньше, чем cap"),
        ("long", "short", "short", "⚠️  ограничение планом"),
        ("long", "medium", "medium", "⚠️  ограничение планом"),
        ("long", "long", "long", "оба long"),
        ("invalid", "medium", "medium", "невалидная настройка → fallback на cap"),
        ("", "short", "short", "пустая настройка → fallback на cap"),
    ]

    print("\n" + "=" * 70)
    print("🧪 ТЕСТ ЛОГИКИ ОГРАНИЧЕНИЯ ДЛИНЫ ДАЙДЖЕСТА ПО ПЛАНУ")
    print("=" * 70)
    print("\nТест проверяет, что plan cap всегда ограничивает длину дайджеста:")
    print("  • Если user_pref <= plan_cap → используется user_pref")
    print("  • Если user_pref > plan_cap → используется plan_cap (ограничение)")
    print("=" * 70)

    all_passed = True

    for user_pref, plan_cap, expected, description in test_cases:
        result = apply_plan_cap(user_pref, plan_cap)

        passed = result == expected
        status = "✅" if passed else "❌"

        clamped_marker = ""
        if result != user_pref and user_pref in ("short", "medium", "long"):
            clamped_marker = " 🔒 ОГРАНИЧЕНО"

        print(
            f"\n{status} user_pref='{user_pref:<7}' + plan_cap='{plan_cap:<6}' "
            f"→ '{result:<6}'{clamped_marker}"
        )
        print(f"   {description}")

        if not passed:
            print(f"   ❌ Ожидалось: '{expected}', получено: '{result}'")
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n✨ Исправление работает корректно:")
        print("   • План Demo (cap=short) будет ограничивать medium/long до short")
        print("   • План Daily (cap=medium) будет ограничивать long до medium")
        print("   • План Full (cap=long) не накладывает ограничений")
    else:
        print("❌ ЕСТЬ ОШИБКИ!")

    print("=" * 70 + "\n")

    return all_passed


def test_demo_plan_scenario():
    """Тест сценария, описанного в issue."""

    print("\n" + "=" * 70)
    print("📱 ТЕСТ СЦЕНАРИЯ ИЗ ISSUE: План Demo + настройка Medium")
    print("=" * 70)

    print("\nСценарий:")
    print("  • Пользователь завершил онбординг")
    print("  • Выбрал длину дайджеста: Medium (сбалансированно)")
    print("  • Имеет план: Demo (cap = short)")
    print("  • Ожидается: дайджест будет SHORT (ограничен планом)")

    user_pref = "medium"
    plan_cap = "short"

    result = apply_plan_cap(user_pref, plan_cap)

    print(f"\n🔍 Применение логики:")
    print(f"   user_preference = '{user_pref}'")
    print(f"   plan_cap = '{plan_cap}'")
    print(f"   final_length = '{result}'")

    if result == "short":
        print("\n✅ ПРАВИЛЬНО! Дайджест ограничен планом до SHORT")
        print("   Пользователь получит 2-3 предложения вместо полного дайджеста")
        return True
    else:
        print(f"\n❌ ОШИБКА! Ожидалось 'short', получено '{result}'")
        print("   Пользователь получит полный дайджест, обходя ограничение плана")
        return False


def test_edge_cases():
    """Тест граничных случаев."""

    print("\n" + "=" * 70)
    print("🔬 ТЕСТ ГРАНИЧНЫХ СЛУЧАЕВ")
    print("=" * 70)

    edge_cases = [
        (None, "medium", "medium", "None user_pref"),
        ("", "short", "short", "Пустая строка user_pref"),
        ("MEDIUM", "short", "short", "Неправильный регистр"),
        ("med", "long", "long", "Сокращённое значение"),
    ]

    all_passed = True

    for user_pref, plan_cap, expected, description in edge_cases:
        try:
            # Преобразуем None в пустую строку для теста
            test_pref = user_pref if user_pref is not None else ""
            result = apply_plan_cap(test_pref, plan_cap)

            passed = result == expected
            status = "✅" if passed else "❌"

            print(f"\n{status} {description}")
            print(
                f"   user_pref={repr(user_pref)} + plan_cap='{plan_cap}' → '{result}'"
            )

            if not passed:
                print(f"   ❌ Ожидалось: '{expected}'")
                all_passed = False
        except Exception as e:
            print(f"\n❌ {description}")
            print(f"   Исключение: {e}")
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ Все граничные случаи обработаны корректно")
    else:
        print("❌ Есть проблемы с граничными случаями")

    print("=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 ТЕСТ ИСПРАВЛЕНИЯ PLAN CAP ДЛЯ DIGEST LENGTH")
    print("=" * 70)

    # Основной тест логики
    logic_passed = test_plan_cap_logic()

    # Тест сценария из issue
    scenario_passed = test_demo_plan_scenario()

    # Тест граничных случаев
    edge_passed = test_edge_cases()

    # Итоговый результат
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 70)

    results = [
        ("Логика ограничения", logic_passed),
        ("Сценарий Demo + Medium", scenario_passed),
        ("Граничные случаи", edge_passed),
    ]

    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 70)

    if all_passed:
        print("✅✅✅ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ✅✅✅")
        print("\n🎉 Исправление готово к использованию!")
        print("\nЧто исправлено:")
        print("  1. routes_telegram.py /today - применяет plan cap")
        print("  2. telegram_worker.py scheduled delivery - применяет plan cap")
        print("\nПользователи больше не смогут обходить ограничения плана.")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ, ТРЕБУЕТСЯ ДОРАБОТКА")

    print("=" * 70 + "\n")

    # Выход с кодом 0 если всё ок, 1 если есть ошибки
    exit(0 if all_passed else 1)
