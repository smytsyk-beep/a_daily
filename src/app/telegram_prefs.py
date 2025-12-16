# src/app/telegram_prefs.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app import models


# Дефолты для настроек доставки в Telegram
DEFAULT_DELIVERY_TIME_LOCAL = "08:00"
DEFAULT_DELIVERY_ENABLED = True
DEFAULT_QUIET_MODE = False


@dataclass
class TelegramDeliveryPrefs:
    """
    Нормализованные настройки Telegram-доставки для пользователя.
    """

    user_id: int
    time_local: str  # "HH:MM" локальное время отправки дайджеста
    enabled: bool  # включена ли ежедневная доставка
    quiet_mode: bool  # включён ли quiet mode


def _normalize_time_local(raw: Optional[str]) -> str:
    """
    Простейшая нормализация времени.
    Ожидаем формат "HH:MM"; если что-то не так — возвращаем дефолт.
    """
    if not raw:
        return DEFAULT_DELIVERY_TIME_LOCAL

    raw = raw.strip()
    parts = raw.split(":")

    if len(parts) != 2:
        return DEFAULT_DELIVERY_TIME_LOCAL

    try:
        hh = int(parts[0])
        mm = int(parts[1])
    except ValueError:
        return DEFAULT_DELIVERY_TIME_LOCAL

    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return DEFAULT_DELIVERY_TIME_LOCAL

    return f"{hh:02d}:{mm:02d}"


def get_telegram_prefs_from_user(user: models.User) -> TelegramDeliveryPrefs:
    """
    Строит TelegramDeliveryPrefs из модели User,
    подставляя дефолты, если поля ещё не заполнены.

    Маппинг:
      - time_local <- user.delivery_time_local (нормализуем в "HH:MM")
      - enabled    <- user.delivery_enabled (если None -> DEFAULT_DELIVERY_ENABLED)
      - quiet_mode <- user.quiet_mode (если None -> DEFAULT_QUIET_MODE)
    """
    time_local = _normalize_time_local(user.delivery_time_local)

    enabled = (
        DEFAULT_DELIVERY_ENABLED
        if user.delivery_enabled is None
        else bool(user.delivery_enabled)
    )

    quiet_mode = (
        DEFAULT_QUIET_MODE if user.quiet_mode is None else bool(user.quiet_mode)
    )

    return TelegramDeliveryPrefs(
        user_id=user.id,
        time_local=time_local,
        enabled=enabled,
        quiet_mode=quiet_mode,
    )
