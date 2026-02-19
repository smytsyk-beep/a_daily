#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование унифицированного геокодера с поддержкой русского языка.

Использует новый app.services.geocoder в stub mode (без внешних API).
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock

# Установка правильной кодировки для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.services.geocoder import get_geocoder_service


def test_geocoder():
    """Тестирует геокодер с различными вводами."""
    
    test_cases = [
        # Украина (русский)
        "Киев, Украина",
        "Харьков, Украина",
        "Одесса, Украина",
        "Львов, Украина",
        # Украина (английский)
        "Kyiv, Ukraine",
        "Kharkiv, Ukraine",
        "Odesa, Ukraine",
        "Lviv, Ukraine",
        # Украина (украинский)
        "Київ, Україна",
        "Харків, Україна",
        "Одеса, Україна",
        "Львів, Україна",
        # Россия
        "Москва, Россия",
        "Санкт-Петербург, Россия",
        "Питер, Россия",
        "Moscow, Russia",
        # США
        "Нью-Йорк, США",
        "Лос-Анджелес, США",
        "New York, USA",
        "Los Angeles, USA",
        # Другие страны
        "Минск, Беларусь",
        "Кишинев, Молдова",
        "Стамбул, Турция",
        "Мадрид, Испания",
        "Лондон, Великобритания",
        "Алматы, Казахстан",
        # Только страна
        "Украина",
        "Россия",
        "США",
        # Некорректные
        "Неизвестный город",
        "Atlantis",
        "",
    ]
    
    print("="*70)
    print("ТЕСТИРОВАНИЕ УНИФИЦИРОВАННОГО ГЕОКОДЕРА (STUB MODE)")
    print("="*70)
    print()
    
    # Создаём mock БД для stub mode (без реальной БД)
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Инициализируем geocoder в stub mode (только hardcoded fallback)
    geocoder = get_geocoder_service(mock_db, mode="stub")
    
    success = 0
    failed = 0
    
    for place in test_cases:
        result = geocoder.geocode(place, language="ru")
        
        if result:
            print(f"[OK] '{place}'")
            print(f"     -> {result.display_name}")
            print(f"     -> ({result.lat:.4f}, {result.lon:.4f})")
            print(f"     -> provider: {result.provider}")
            print()
            success += 1
        else:
            print(f"[FAIL] '{place}' -> не найдено")
            print()
            failed += 1
    
    print("="*70)
    print(f"РЕЗУЛЬТАТЫ: {success} успешно, {failed} не найдено")
    print("="*70)
    print()
    print("NOTE: Stub mode использует только hardcoded fallback.")
    print("      Для полного покрытия используйте mode='chain' с реальной БД.")
    print("="*70)
    
    return failed == 0


def main():
    """Главная функция."""
    
    success = test_geocoder()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
