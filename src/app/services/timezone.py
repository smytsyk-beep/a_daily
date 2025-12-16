# src/app/services/timezone.py
from __future__ import annotations

from functools import lru_cache
from typing import Optional

try:
    from timezonefinder import TimezoneFinder  # type: ignore[import]
except ImportError:  # мягкий fallback
    TimezoneFinder = None  # type: ignore[assignment]


@lru_cache(maxsize=1)
def _get_tf() -> "TimezoneFinder":
    """
    Ленивая инициализация TimezoneFinder.

    Если пакет не установлен, кидаем RuntimeError — чтобы
    было понятно в dev/тестах, что нужно добавить зависимость.
    """
    if TimezoneFinder is None:
        raise RuntimeError(
            "timezonefinder не установлен. "
            "Добавь пакет 'timezonefinder' в зависимости приложения."
        )

    return TimezoneFinder()  # type: ignore[no-any-return]


def tz_by_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Возвращает IANA-таймзону по широте/долготе, например "Europe/Berlin".

    Поведение:
    - если timezonefinder не установлен → возвращаем None;
    - если библиотека ничего не нашла → тоже None.
    """
    if TimezoneFinder is None:
        # нет зависимости — считаем, что фича не активна
        return None

    tf = _get_tf()
    tz = tf.timezone_at(lat=lat, lng=lon)
    # timezone_at может вернуть None
    return tz or None
