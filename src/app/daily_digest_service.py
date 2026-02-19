# src/app/daily_digest_service.py

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from common.config import get_settings
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
      - user.prefs (если есть)  → focus_topics, digest_interests, text_length
      - user.digest_interests / user.digest_length_preference как фолбек
    """
    # Локаль
    locale = user.locale or "en"

    # prefs из JSONB (может быть None)
    prefs = getattr(user, "prefs", None) or {}

    # --- Интересы ---
    # Приоритет:
    #   1) prefs["focus_topics"] или prefs["digest_interests"] (онбординг)
    #   2) user.digest_interests
    #   3) ["general"]
    interests = (
        prefs.get("focus_topics")
        or prefs.get("digest_interests")
        or getattr(user, "digest_interests", None)
        or ["general"]
    )

    # Приводим к списку строк
    if not isinstance(interests, list):
        interests = [str(interests)]
    interests = [str(x).strip() for x in interests if str(x).strip()]
    if not interests:
        interests = ["general"]

    # --- Предпочитаемая длина текста ---
    # Приоритет:
    #   1) prefs["text_length"] или prefs["digest_length_preference"]
    #   2) user.digest_length_preference
    #   3) "medium"
    preferred_length = (
        prefs.get("text_length")
        or prefs.get("digest_length_preference")
        or getattr(user, "digest_length_preference", None)
        or "medium"
    )
    if preferred_length not in ("short", "medium", "long"):
        preferred_length = "medium"

    return UserProfile(
        locale=locale,
        interests=interests,
        preferred_length=preferred_length,
        delivery_time_local=getattr(user, "delivery_time_local", None),
    )


def _compute_max_atoms(preferred_length: str, plan_code: Optional[str]) -> int:
    """
    Определяем, сколько атомов максимум можно брать в дайджест.

    Логика:
    1. Берём plan_config.digest_cap из плана (short/medium/long)
    2. Если у пользователя preferred_length выше, чем план позволяет — ограничиваем планом
    3. Конвертируем в количество атомов:
       short  → 2 атома  (краткий обзор, 1-2 абзаца)
       medium → 3 атома  (сбалансированный, 2-3 абзаца)
       long   → 6 атомов (подробный, 3-6 абзацев)

    Для плана demo — всегда не больше 2 атомов (план Demo cap=short).
    """
    from common.plans import get_plan_config, normalise_plan_code

    # Нормализуем plan_code
    plan = normalise_plan_code(plan_code)
    plan_cfg = get_plan_config(plan)

    # Ограничение плана
    plan_cap = plan_cfg.digest_cap  # "short" | "medium" | "long"

    # Иерархия длин для сравнения
    length_hierarchy = {"short": 1, "medium": 2, "long": 3}

    # Эффективная длина: минимум из (preferred_length, plan_cap)
    effective_length = preferred_length
    if length_hierarchy.get(preferred_length, 2) > length_hierarchy.get(plan_cap, 2):
        effective_length = plan_cap

    # Конвертируем в количество атомов
    max_atoms = 3  # default для medium

    if effective_length == "short":
        max_atoms = 2
    elif effective_length == "long":
        max_atoms = 6
    elif effective_length == "medium":
        max_atoms = 3

    return max_atoms


def build_daily_digest_for_user(
    db: Session,
    user: models.User,
    *,
    today: Optional[date] = None,
    length: Optional[str] = None,
) -> DailyDigestText:
    """
    Основной вход: строит текст ежедневного дайджеста для пользователя.

    - db      — SQLAlchemy Session
    - user    — объект модели User
    - today   — дата, для которой считаем дайджест (по умолчанию — сегодня)
    - length  — "short" / "medium" / "long" (если None — из профиля/плана)
    """
    import logging

    logger = logging.getLogger(__name__)

    day = today or date.today()

    logger.info(
        "[DIGEST_SERVICE] build_daily_digest_for_user: user_id=%d, day=%s, length_override=%s",
        user.id,
        day,
        length,
    )

    # 1. План пользователя (читаем всегда!)
    plan_code: Optional[str] = None
    try:
        plan_code = get_user_plan(db, user.id)
        logger.info("[DIGEST_SERVICE] User plan: %s", plan_code)
    except Exception as e:
        logger.warning("[DIGEST_SERVICE] Failed to get user plan: %s", e)
        plan_code = None

    # Для плана demo принудительно ставим short, если length не задан явно
    length_override = length
    if length_override is None and plan_code == "demo":
        length_override = "short"
        logger.info("[DIGEST_SERVICE] Demo plan detected, forcing length=short")

    # 2. Профиль пользователя
    user_profile = make_user_profile_from_model(user)

    logger.info(
        "[DIGEST_SERVICE] User profile: interests=%s, preferred_length=%s",
        user_profile.interests,
        user_profile.preferred_length,
    )

    # 3. Определяем финальную длину для выборки атомов
    # Если length_override передан - используем его, иначе - из профиля
    effective_length = (
        length_override if length_override else user_profile.preferred_length
    )

    logger.info(
        "[DIGEST_SERVICE] Effective length for atom selection: %s", effective_length
    )

    # 4. Максимум атомов (теперь используем effective_length)
    max_atoms = _compute_max_atoms(
        preferred_length=effective_length,
        plan_code=plan_code,
    )

    logger.info(
        "[DIGEST_SERVICE] Computed max_atoms=%d (plan=%s, length=%s)",
        max_atoms,
        plan_code,
        effective_length,
    )

    # 5. Подбор атомов по транзитам и глобальным событиям
    selected_atoms = select_atoms_for_day(
        db=db,
        user_id=user.id,
        day=day,
        user_profile=user_profile,
        max_total_atoms=max_atoms,
    )

    logger.info(
        "[DIGEST_SERVICE] Selected %d atoms from RAG layer (max requested: %d)",
        len(selected_atoms),
        max_atoms,
    )

    # Логируем выбранные атомы для отладки
    for i, sel in enumerate(selected_atoms, 1):
        logger.debug(
            "[DIGEST_SERVICE] RAG Atom %d: id=%d, trigger=%s, persona_tags=%s, score=%.2f",
            i,
            sel.atom.id,
            sel.atom.trigger,
            sel.atom.persona_tags,
            sel.score,
        )

    # 5a. Тихий день — общие day_general_* атомы
    if not selected_atoms:
        logger.info("[DIGEST_SERVICE] No atoms from RAG, trying general day atoms")
        general_atoms = select_general_day_atoms(
            db=db,
            user_profile=user_profile,
            max_atoms=max_atoms,
        )
        if general_atoms:
            logger.info(
                "[DIGEST_SERVICE] Using %d general day atoms", len(general_atoms)
            )
            for i, sel in enumerate(general_atoms, 1):
                logger.debug(
                    "[DIGEST_SERVICE] General Atom %d: id=%d, topic_tag=%s",
                    i,
                    sel.atom.id,
                    sel.atom.topic_tag,
                )
            selected_atoms = general_atoms
        else:
            logger.info("[DIGEST_SERVICE] No general atoms found either")
    # 5b. Если атомов меньше чем max_atoms — дополняем general day atoms
    elif len(selected_atoms) < max_atoms:
        logger.info(
            "[DIGEST_SERVICE] Only %d atoms from RAG (requested %d), adding general day atoms",
            len(selected_atoms),
            max_atoms,
        )
        remaining = max_atoms - len(selected_atoms)
        general_atoms = select_general_day_atoms(
            db=db,
            user_profile=user_profile,
            max_atoms=remaining,
        )
        if general_atoms:
            logger.info(
                "[DIGEST_SERVICE] Adding %d general day atoms", len(general_atoms)
            )
            for i, sel in enumerate(general_atoms, 1):
                logger.debug(
                    "[DIGEST_SERVICE] General Atom %d: id=%d, topic_tag=%s",
                    i,
                    sel.atom.id,
                    sel.atom.topic_tag,
                )
            selected_atoms.extend(general_atoms)
            logger.info(
                "[DIGEST_SERVICE] Total atoms after adding general: %d",
                len(selected_atoms),
            )

    # 6. A/B: назначаем вариант (simple vs llm) по user_id для стабильного сплита
    ab_percent = get_settings().AB_DIGEST_LLM_PERCENT
    use_llm = (hash(user.id) % 100) < ab_percent if user else True

    # 7. Рендерим текст дайджеста
    digest = render_daily_digest_from_atoms(
        atoms=selected_atoms,
        day=day,
        user_profile=user_profile,
        length_override=length_override,
        use_llm=use_llm,
    )

    # 8. Cost tracking: запись в llm_usage_log при использовании LLM
    if getattr(digest, "llm_usage", None) and user:
        usage = digest.llm_usage
        log_entry = models.LLMUsageLog(
            user_id=user.id,
            model=usage["model"],
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            estimated_cost_usd=float(usage["estimated_cost_usd"]),
            cache_hit=usage["cache_hit"],
        )
        db.add(log_entry)
        logger.debug(
            "[DIGEST_SERVICE] LLM usage logged: model=%s, cache_hit=%s",
            usage["model"],
            usage["cache_hit"],
        )

    logger.info(
        "[DIGEST_SERVICE] Digest rendered: %d chars body, %d chars title",
        len(digest.body),
        len(digest.title),
    )

    return digest


def build_daily_digest_for_user_id(
    db: Session,
    user_id: int,
    *,
    today: Optional[date] = None,
    length: Optional[str] = None,
) -> Optional[DailyDigestText]:
    """
    Вспомогательный вход по user_id (удобно для модулей/оркестратора).
    """
    user = db.query(models.User).filter(models.User.id == user_id).one_or_none()
    if user is None:
        return None

    return build_daily_digest_for_user(
        db=db,
        user=user,
        today=today,
        length=length,
    )
