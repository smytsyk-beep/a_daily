# src/app/modules/daily_digest.py
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from app.repo import session_scope, resolve_user_id
from app.daily_digest_service import build_daily_digest_for_user

Atom = Dict[str, Any]


def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    """
    Собирает payload для ежедневного дайджеста.

    Новая логика:
      * через resolve_user_id получаем numeric user_id;
      * вызываем build_daily_digest_for_user, который:
          - подтягивает транзиты и глобальные события,
          - через RAG выбирает ContentAtom'ы,
          - генерирует стабильный текст дайджеста;
      * упаковываем всё это в один Atom, который
        модуль/оркестратор может дальше использовать.

    Формат возвращаемого атома (superset старого контракта):
      {
        "module": "daily_digest",
        "kind": "digest",
        "topic_tag": "generic_day_overview",
        "weight": 1.0,
        "time_local": "08:00",
        "date": "2025-01-10",
        "locale": "en",
        "length": "medium",
        "title": "...",
        "body": "...",
        "affirmation": "...",
        "disclaimer": "..."
      }
    """
    cfg = config or {}

    # Как и раньше, отдаём локальное время в атом,
    # чтобы дальше логика доставки могла его использовать.
    time_local = cfg.get("time_local", "08:00")

    # Возможность принудительно задать длину текста: "short" | "medium" | "long"
    length_override = cfg.get("length")

    today = datetime.utcnow().date()

    with session_scope() as db:
        # user_id сюда приходит как user_ref (tg_user_id и т.п.)
        numeric_user_id = resolve_user_id(db, user_ref=user_id)

        digest = build_daily_digest_for_user(
            db=db,
            user_id=numeric_user_id,
            day=today,
            user_profile=None,  # профиль построится из models.User
            length_override=length_override,
        )

    atom: Atom = {
        "module": "daily_digest",
        "kind": "digest",
        "topic_tag": "generic_day_overview",
        "weight": 1.0,  # при желании потом можно связать с силой событий
        "time_local": time_local,
        # новые поля с текстом дайджеста
        "date": digest.date.isoformat(),
        "locale": digest.locale,
        "length": digest.length,
        "title": digest.title,
        "body": digest.body,
        "affirmation": digest.affirmation,
        "disclaimer": digest.disclaimer,
    }

    return [atom]
