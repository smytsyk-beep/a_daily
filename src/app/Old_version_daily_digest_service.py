# src/app/daily_digest_service.py

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from common.plans import get_user_plan
from app.content_atoms_rag import (
    UserProfile,
    select_atoms_for_day,
    select_general_day_atoms,
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


def _compute_max_atoms(preferred_length: str, plan_code: Optional[str]) -> int:
    """
    Определяем, сколько атомов максимум можно брать в дайджест.

    Базовое правило:
      short  → 2
      medium → 4
      long   → 6

    Для плана demo — всегда не больше 2 атомов.
    """
    max_atoms = 4

    if preferred_length == "short":
        max_atoms = 2
    elif preferred_length == "long":
        max_atoms = 6

    if plan_code == "demo":
        max_atoms = min(max_atoms, 2)

    return max_atoms


def build_daily_digest_for_user(
    db: Session,
    user_id: int,
    *,
    day: date,
    user_profile: Optional[UserProfile] = None,
    length_override: Optional[str] = None,
) -> DailyDigestText:
    """
    Высокоуровневый сервис: строит текст ежедневного дайджеста для пользователя.

    Шаги:
      1) По user_id подтягиваем models.User.
      2) Читаем план пользователя (demo/daily/full/internal).
      3) Собираем UserProfile (локаль, интересы, предпочитаемая длина текста).
      4) Подбираем релевантные контент-атомы на день через select_atoms_for_day
         (транзиты + глобальные события).
      5) Если атомов нет (тихий день) — пробуем взять «общие» day_general_* атомы.
      6) Рендерим итоговый текст через render_daily_digest_from_atoms.
    """

    # 0. Подтягиваем пользователя
    user = db.query(models.User).filter(models.User.id == user_id).one()

    # 1. План пользователя
    plan_code: Optional[str] = None
    if length_override is None:
        try:
            plan_code = get_user_plan(db, user_id)
        except Exception:
            # План не должен ломать основной флоу, просто игнорируем сбои
            plan_code = None

        # Для demo принудительно короткий текст
        if plan_code == "demo":
            length_override = "short"

    # 2. Собираем профиль пользователя (если его не передали извне)
    if user_profile is None:
        user_profile = make_user_profile_from_model(user)

    # 3. Определяем, сколько атомов максимум брать в дайджест
    max_atoms = _compute_max_atoms(
        preferred_length=user_profile.preferred_length,
        plan_code=plan_code,
    )

    # 4. Основной подбор атомов по транзитам и глобальным событиям
    selected_atoms = select_atoms_for_day(
        db=db,
        user_id=user.id,
        day=day,  # ВАЖНО: аргумент называется day, не local_date
        user_profile=user_profile,
        max_total_atoms=max_atoms,
    )

    # 4a. Тихий день: нет транзитных атомов → пробуем общие day_general_* атомы
    if not selected_atoms:
        general_atoms = select_general_day_atoms(
            db=db,
            user_profile=user_profile,
            max_atoms=max_atoms,
        )
        if general_atoms:
            selected_atoms = general_atoms

    # 5. Рендерим итоговый текст дайджеста.
    # Если selected_atoms пуст — render_daily_digest_from_atoms
    # включит внутренний quiet-day фоллбек.
    digest = render_daily_digest_from_atoms(
        atoms=selected_atoms,
        day=day,
        user_profile=user_profile,
        length_override=length_override,
    )

    return digest
