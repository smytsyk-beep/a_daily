# Исправление проблемы с timezone при завершении онбординга

## Проблема

После завершения онбординга:
- В таблице users все поля заполнены, КРОМЕ timezone и delivery_time_local
- В prefs onboarding_state = "complete"
- Все данные рождения заполнены (birth_date, birth_time, birth_place)
- Гео определяется, справочники (geocode_cache) заполнены
- НО при запуске /today выходит сообщение "онбординг не завершён"

## Причина

1. При пропуске геолокации (STATE_ASK_TIMEZONE_LOCATION):
   - Код просто переходил к следующему шагу
   - НЕ устанавливал user.timezone из birth_place
   - Комментарий говорил "используем timezone из birth_place", но код этого не делал

2. В команде /today есть жёсткая проверка:
   ```python
   if not user.timezone:
       send_message("онбординг не завершён")
   ```

3. При завершении онбординга не устанавливалось дефолтное delivery_time_local

## Решение

### 1. Исправлена обработка пропуска геолокации

При пропуске геолокации (STATE_ASK_TIMEZONE_LOCATION):
1. Вызывается ensure_birthdata_geo_for_user(db, user)
   - Геокодирует birth_place
   - Определяет lat/lon
   - Устанавливает timezone в birth_data.tz

2. Берём timezone из birth_data.tz
3. Устанавливаем в user.timezone и prefs["timezone"]
4. Если не удалось определить - fallback на UTC

Код:
```python
if state == STATE_ASK_TIMEZONE_LOCATION:
    # Резолвим timezone из birth_place через BirthData
    ensure_birthdata_geo_for_user(db, user)
    
    # Берём timezone из BirthData и устанавливаем в user.timezone
    birth_data = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user.id)
        .order_by(models.BirthData.id.desc())
        .first()
    )
    
    if birth_data and birth_data.tz:
        user.timezone = birth_data.tz
        prefs["timezone"] = birth_data.tz
    else:
        # Fallback: если не удалось определить timezone, используем UTC
        user.timezone = "UTC"
        prefs["timezone"] = "UTC"
```

### 2. Установка дефолтного delivery_time_local

При завершении онбординга (STATE_ASK_PREFS_DELIVERY):
1. В prefs устанавливается delivery_time_local = "09:00"
2. В модели user устанавливается delivery_time_local = time(9, 0)

Код:
```python
# В prefs
if "delivery_time_local" not in prefs:
    prefs["delivery_time_local"] = "09:00"

# В модели
if hasattr(user, "delivery_time_local"):
    if not user.delivery_time_local:
        from datetime import time as time_type
        user.delivery_time_local = time_type(9, 0)
```

## Изменённые файлы

- src/app/routes_telegram.py
  - Обработка STATE_ASK_TIMEZONE_LOCATION (строки ~354-397)
  - Установка дефолтного delivery_time_local при завершении онбординга (строки ~470-510)

## Тестирование

Запустите:
```
python scripts/test_timezone_fix.py
```

Или протестируйте вручную:
1. Начните онбординг с нового пользователя
2. Пройдите до этапа "поделиться локацией"
3. Нажмите "Пропустить" или введите любой текст
4. Завершите онбординг
5. Введите /today
6. Должен прийти дайджест (не ошибка "онбординг не завершён")

## Важно

После этого исправления:
- user.timezone ВСЕГДА устанавливается при завершении онбординга
- Используется timezone из birth_place через геокодирование
- Если не удалось определить - используется UTC
- /today работает сразу после завершения онбординга

## Для существующих пользователей

Если у вас есть пользователи с завершённым онбордингом но без timezone:

1. Можно создать миграционный скрипт:
   - Найти всех пользователей где onboarding_state = "complete" но timezone = NULL
   - Для каждого вызвать ensure_birthdata_geo_for_user
   - Установить user.timezone из birth_data.tz
   - Fallback на UTC если не удалось

2. Или они могут использовать /continue для продолжения онбординга
