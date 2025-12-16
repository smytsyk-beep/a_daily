# src/app/daily_digest_service.py
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.content_atoms_rag import (
    UserProfile,
    select_atoms_for_day,
)
from app.text_generation import (
    DailyDigestText,
    render_daily_digest_from_atoms,
)


def make_user_profile_from_model(user: models.User) -> UserProfile:
    """
    Превращает models.User в UserProfile.

    Используем:
      - user.locale
      - user.prefs (если есть)  → focus_topics, text_length
      - user.digest_interests / user.digest_length_preference как фолбек
    """
    # Локаль
    locale = user.locale or "en"

    # prefs из JSONB (может быть None)
    prefs = getattr(user, "prefs", None) or {}

    # --- Интересы ---
    # Приоритет:
    #   1) prefs["focus_topics"]
    #   2) user.digest_interests
    #   3) ["general"]
    interests = prefs.get("focus_topics") or user.digest_interests or ["general"]

    # Приводим к списку строк
    if not isinstance(interests, list):
        interests = [str(interests)]
    interests = [str(x).strip() for x in interests if str(x).strip()]
    if not interests:
        interests = ["general"]

    # --- Предпочитаемая длина текста ---
    # Приоритет:
    #   1) prefs["text_length"]
    #   2) user.digest_length_preference
    #   3) "medium"
    preferred_length = (
        prefs.get("text_length") or user.digest_length_preference or "medium"
    )
    if preferred_length not in ("short", "medium", "long"):
        preferred_length = "medium"

    return UserProfile(
        locale=locale,
        interests=interests,
        preferred_length=preferred_length,
        delivery_time_local=user.delivery_time_local,
    )


def build_daily_digest_for_user(
    db: Session,
    user_id: int,
    day: date,
    user_profile: Optional[UserProfile] = None,
    *,
    length_override: Optional[str] = None,
) -> DailyDigestText:
    """
    Главный сервис формирования дневного дайджеста.

    Шаги:
      1) (опц.) строим UserProfile из модели User, если не передан явно;
      2) через select_atoms_for_day получаем релевантные контент-атомы
         (на основе транзитов + глобальных событий);
      3) через render_daily_digest_from_atoms строим текст дайджеста
         с заголовком, текстом, аффирмацией и дисклеймером.

    Этот сервис дальше можно использовать:
      - в HTTP эндпоинте /digest/daily;
      - в оркестраторе /orchestrator/preview;
      - в Telegram-воркере для ежедневных рассылок.
    """
    if user_profile is None:
        user = db.query(models.User).filter(models.User.id == user_id).one()
        user_profile = make_user_profile_from_model(user)

    selected_atoms = select_atoms_for_day(
        db=db,
        user_id=user_id,
        day=day,
        user_profile=user_profile,
        max_total_atoms=4,
    )

    digest = render_daily_digest_from_atoms(
        atoms=selected_atoms,
        day=day,
        user_profile=user_profile,
        length_override=length_override,
    )

    return digest
