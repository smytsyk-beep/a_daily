# src/app/i18n.py

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

SUPPORTED_LOCALES = ("en", "ru", "es")
DEFAULT_LOCALE = "en"

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def normalize_locale(raw: str | None) -> str:
    """
    Telegram присылает language_code вроде 'en', 'ru', 'es', 'uk', 'pt-br'.
    Нормализуем до поддерживаемых en/ru/es.
    """
    if not raw:
        return DEFAULT_LOCALE
    raw = raw.strip().lower()
    base = raw.split("-")[0]

    if base in SUPPORTED_LOCALES:
        return base

    # Частый кейс: uk -> ru (пока нет UA локали)
    if base == "uk":
        return "ru"

    return DEFAULT_LOCALE


@lru_cache(maxsize=16)
def _load_locale(locale: str) -> dict[str, Any]:
    path = _LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _deep_get(d: Mapping[str, Any], key: str) -> Any:
    cur: Any = d
    for part in key.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


def tr(locale: str | None, key: str, **kwargs: Any) -> str:
    """
    Перевод по ключу, безопасный к отсутствующим ключам и плейсхолдерам.

    Fallback: user_locale -> DEFAULT_LOCALE -> ru -> es -> key
    """
    loc = normalize_locale(locale)

    val = _deep_get(_load_locale(loc), key)

    if val is None and loc != DEFAULT_LOCALE:
        val = _deep_get(_load_locale(DEFAULT_LOCALE), key)

    if val is None and "ru" in SUPPORTED_LOCALES and loc != "ru":
        val = _deep_get(_load_locale("ru"), key)

    if val is None and "es" in SUPPORTED_LOCALES and loc != "es":
        val = _deep_get(_load_locale("es"), key)

    if not isinstance(val, str):
        return key

    try:
        return val.format(**kwargs)
    except Exception:
        return val
