# tests/test_telegram_prefs.py
from app import models
from app.telegram_prefs import (
    get_telegram_prefs_from_user,
    DEFAULT_DELIVERY_TIME_LOCAL,
    DEFAULT_DELIVERY_ENABLED,
    DEFAULT_QUIET_MODE,
)


def test_telegram_prefs_defaults_when_fields_none():
    user = models.User(
        id=1,
        tg_user_id="test_user",
        locale="en",
        delivery_time_local=None,
        delivery_enabled=None,
        quiet_mode=None,
    )

    prefs = get_telegram_prefs_from_user(user)

    assert prefs.user_id == 1
    assert prefs.time_local == DEFAULT_DELIVERY_TIME_LOCAL
    assert prefs.enabled == DEFAULT_DELIVERY_ENABLED
    assert prefs.quiet_mode == DEFAULT_QUIET_MODE


def test_telegram_prefs_respects_user_values():
    user = models.User(
        id=2,
        tg_user_id="test_user2",
        locale="en",
        delivery_time_local="21:30",
        delivery_enabled=False,
        quiet_mode=True,
    )

    prefs = get_telegram_prefs_from_user(user)

    assert prefs.user_id == 2
    assert prefs.time_local == "21:30"
    assert prefs.enabled is False
    assert prefs.quiet_mode is True


def test_telegram_prefs_normalizes_bad_time():
    user = models.User(
        id=3,
        tg_user_id="test_user3",
        locale="en",
        delivery_time_local="99:99",  # ерунда
        delivery_enabled=True,
        quiet_mode=False,
    )

    prefs = get_telegram_prefs_from_user(user)

    assert prefs.time_local == DEFAULT_DELIVERY_TIME_LOCAL
