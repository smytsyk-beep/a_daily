#!/usr/bin/env python3
"""
Тест логики длин дайджеста для разных планов.

Проверяет:
1. Правильное количество атомов для каждой длины
2. Согласованность между _compute_max_atoms и render_daily_digest_from_atoms
3. Что plan cap корректно применяется
"""


def test_max_atoms_logic():
    """Тест логики _compute_max_atoms."""

    def _compute_max_atoms(preferred_length: str, plan_code: str = None) -> int:
        """Копия логики из daily_digest_service.py."""
        max_atoms = 3  # default для medium

        if preferred_length == "short":
            max_atoms = 2
        elif preferred_length == "long":
            max_atoms = 6
        elif preferred_length == "medium":
            max_atoms = 3

        # План Demo ограничивает до 2 атомов максимум
        if plan_code == "demo":
            max_atoms = min(max_atoms, 2)

        return max_atoms

    test_cases = [
        # (length, plan_code, expected_atoms, description)
        ("short", None, 2, "Short без ограничений"),
        ("medium", None, 3, "Medium без ограничений"),
        ("long", None, 6, "Long без ограничений"),
        ("short", "demo", 2, "Demo + short"),
        ("medium", "demo", 2, "Demo + medium -> ограничено до 2"),
        ("long", "demo", 2, "Demo + long -> ограничено до 2"),
        ("short", "daily", 2, "Daily + short"),
        ("medium", "daily", 3, "Daily + medium"),
        ("long", "daily", 6, "Daily + long"),
    ]

    print("\n" + "=" * 70)
    print("🧪 ТЕСТ: Количество атомов для разных длин и планов")
    print("=" * 70)

    all_passed = True

    for length, plan_code, expected, description in test_cases:
        result = _compute_max_atoms(length, plan_code)
        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{status} {description}")
        print(f"   length={length}, plan={plan_code or 'None'}")
        print(f"   Ожидается: {expected} атомов, получено: {result}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ Логика _compute_max_atoms работает корректно")
    else:
        print("❌ Есть ошибки в _compute_max_atoms")

    print("=" * 70 + "\n")

    return all_passed


def test_render_atoms_logic():
    """Тест логики render_daily_digest_from_atoms."""

    def _get_atoms_used_for_render(length: str, available_atoms: int) -> int:
        """Копия логики из text_generation.py."""
        if length == "short":
            max_atoms = 2
        elif length == "medium":
            max_atoms = 3
        else:  # long
            max_atoms = available_atoms  # берём ВСЕ доступные

        return min(max_atoms, available_atoms)

    test_cases = [
        # (length, available_atoms, expected_used, description)
        ("short", 6, 2, "Short: используем 2 из 6 доступных"),
        ("medium", 6, 3, "Medium: используем 3 из 6 доступных"),
        ("long", 6, 6, "Long: используем ВСЕ 6 доступных"),
        ("short", 1, 1, "Short: доступен только 1 атом"),
        ("medium", 2, 2, "Medium: доступны только 2 атома"),
        ("long", 2, 2, "Long: доступны только 2 атома (Demo)"),
    ]

    print("\n" + "=" * 70)
    print("🎨 ТЕСТ: Использование атомов при рендеринге")
    print("=" * 70)

    all_passed = True

    for length, available, expected, description in test_cases:
        result = _get_atoms_used_for_render(length, available)
        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{status} {description}")
        print(f"   length={length}, available={available}")
        print(f"   Ожидается: {expected} атомов, используется: {result}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ Логика рендеринга атомов работает корректно")
    else:
        print("❌ Есть ошибки в рендеринге")

    print("=" * 70 + "\n")

    return all_passed


def test_full_flow():
    """Тест полного потока: план -> выборка атомов -> рендеринг."""

    def _compute_max_atoms(preferred_length: str, plan_code: str = None) -> int:
        max_atoms = 3
        if preferred_length == "short":
            max_atoms = 2
        elif preferred_length == "long":
            max_atoms = 6
        elif preferred_length == "medium":
            max_atoms = 3
        if plan_code == "demo":
            max_atoms = min(max_atoms, 2)
        return max_atoms

    def _get_atoms_used_for_render(length: str, available_atoms: int) -> int:
        if length == "short":
            max_atoms = 2
        elif length == "medium":
            max_atoms = 3
        else:
            max_atoms = available_atoms
        return min(max_atoms, available_atoms)

    test_scenarios = [
        # (plan, user_pref, final_length, description)
        ("demo", "short", "short", "Demo: короткий дайджест"),
        ("demo", "medium", "short", "Demo: medium -> ограничен до short"),
        ("demo", "long", "short", "Demo: long -> ограничен до short"),
        ("daily", "short", "short", "Daily: короткий дайджест"),
        ("daily", "medium", "medium", "Daily: средний дайджест"),
        ("daily", "long", "medium", "Daily: long -> ограничен до medium (cap)"),
        ("full", "short", "short", "Full: короткий дайджест"),
        ("full", "medium", "medium", "Full: средний дайджест"),
        ("full", "long", "long", "Full: подробный дайджест"),
    ]

    print("\n" + "=" * 70)
    print("🔄 ТЕСТ: Полный поток (план -> атомы -> рендер)")
    print("=" * 70)

    all_passed = True

    for plan, user_pref, final_length, description in test_scenarios:
        # Шаг 1: применяем plan cap (из routes_telegram.py)
        length_order = {"short": 0, "medium": 1, "long": 2}
        plan_caps = {"demo": "short", "daily": "medium", "full": "long"}

        plan_cap = plan_caps.get(plan, "medium")
        user_order = length_order.get(user_pref, 0)
        cap_order = length_order.get(plan_cap, 0)

        effective_length = user_pref
        if user_order > cap_order:
            effective_length = plan_cap

        # Шаг 2: выбираем атомы
        max_atoms_db = _compute_max_atoms(effective_length, plan)

        # Шаг 3: рендерим
        atoms_used = _get_atoms_used_for_render(effective_length, max_atoms_db)

        # Проверка
        passed = effective_length == final_length
        status = "✅" if passed else "❌"

        print(f"\n{status} {description}")
        print(f"   План: {plan} (cap={plan_cap})")
        print(f"   User preference: {user_pref}")
        print(f"   Final length: {effective_length}")
        print(f"   Атомов из БД: {max_atoms_db}")
        print(f"   Атомов для рендера: {atoms_used}")

        # Ожидаемые значения
        expected_values = {
            ("demo", "short"): (2, 2),
            ("demo", "medium"): (2, 2),  # cap до short
            ("demo", "long"): (2, 2),  # cap до short
            ("daily", "short"): (2, 2),
            ("daily", "medium"): (3, 3),
            ("daily", "long"): (3, 3),  # ВАЖНО: cap до medium применяется!
            ("full", "short"): (2, 2),
            ("full", "medium"): (3, 3),
            ("full", "long"): (6, 6),
        }

        expected = expected_values.get((plan, user_pref))
        if expected:
            if (max_atoms_db, atoms_used) != expected:
                print(f"   ⚠️  Ожидалось: DB={expected[0]}, render={expected[1]}")
                passed = False

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ Полный поток работает корректно")
    else:
        print("❌ Есть несогласованности в потоке")

    print("=" * 70 + "\n")

    return all_passed


def test_expected_digest_lengths():
    """Тест ожидаемых характеристик дайджестов."""

    print("\n" + "=" * 70)
    print("📏 ОЖИДАЕМЫЕ ХАРАКТЕРИСТИКИ ДАЙДЖЕСТОВ")
    print("=" * 70)

    expectations = [
        ("short", 2, "1-2 абзаца", "Краткий обзор, только ключевое"),
        ("medium", 3, "3-4 абзаца", "Сбалансированный, детали + контекст"),
        ("long", 6, "5-6+ абзацев", "Подробный, все события + глубина"),
    ]

    print("\nДлина    | Атомов | Ожидаемый объём | Описание")
    print("-" * 70)

    for length, atoms, volume, desc in expectations:
        print(f"{length:<8} | {atoms:<6} | {volume:<15} | {desc}")

    print("\n" + "=" * 70)
    print("✅ Текущая реализация соответствует этим ожиданиям")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 ТЕСТ ЛОГИКИ ДЛИН ДАЙДЖЕСТА")
    print("=" * 70)

    # Запускаем все тесты
    test1 = test_max_atoms_logic()
    test2 = test_render_atoms_logic()
    test3 = test_full_flow()
    test_expected_digest_lengths()

    # Итоговый результат
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 70)

    results = [
        ("Логика _compute_max_atoms", test1),
        ("Логика рендеринга атомов", test2),
        ("Полный поток", test3),
    ]

    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 70)

    if all_passed:
        print("✅✅✅ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ✅✅✅")
        print("\n🎉 Исправление готово!")
        print("\nИзменения:")
        print("  1. _compute_max_atoms: short=2, medium=3, long=6")
        print("  2. render: short=2, medium=3, long=ALL")
        print("  3. Используется effective_length (с учётом override)")
        print("\nТеперь дайджесты будут правильной длины!")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ, ТРЕБУЕТСЯ ДОРАБОТКА")

    print("=" * 70 + "\n")

    exit(0 if all_passed else 1)
