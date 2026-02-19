# src/app/text_generation.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.content_atoms_rag import SelectedAtom, UserProfile
from app.astro.global_events import compute_global_events

logger = logging.getLogger(__name__)

DISCLAIMER_EN = (
    "This content is for entertainment and general inspiration only and "
    "is not medical, financial, or legal advice."
)


@dataclass
class DailyDigestText:
    """
    Результат генерации текста для дневного дайджеста.

    Это то, что потом будет уходить в /digest/daily и Telegram.
    llm_usage — при использовании LLM: данные для записи в llm_usage_log (cost tracking).
    """

    date: date
    locale: str
    length: str  # "short" | "medium" | "long"
    title: str
    body: str
    affirmation: Optional[str]
    disclaimer: str
    llm_usage: Optional[dict] = (
        None  # model, prompt_tokens, completion_tokens, estimated_cost_usd, cache_hit
    )
    render_variant: str = "simple"  # "simple" | "llm" — для A/B анализа


def _pick_effective_length(
    user_profile: Optional[UserProfile],
    length_override: Optional[str],
) -> str:
    if length_override in ("short", "medium", "long"):
        return length_override
    if user_profile and user_profile.preferred_length in ("short", "medium", "long"):
        return user_profile.preferred_length
    return "medium"


def _fallback_text(locale: str, length: str, day: date) -> DailyDigestText:
    """
    Fallback-текст на "тихий" день.

    Теперь он учитывает фазу Луны через compute_global_events.
    """
    # Пытаемся получить фазу Луны на указанный день
    phase_name: Optional[str] = None
    try:
        events = compute_global_events(day, day)
        for ev in events:
            if ev.kind == "moon_phase":
                phase_name = ev.name or ev.payload.get("phase")
                break
    except Exception:
        # на всякий случай не ломаемся, если что-то пошло не так
        phase_name = None

    if phase_name:
        title = f"Quiet day with the {phase_name}"
        body = (
            f"Today the Moon is in a {phase_name} phase. "
            "It's a relatively calm day in the sky, so it's a good moment "
            "to focus on simple, grounded actions and gentle self-care."
        )
    else:
        title = "A quiet day in the stars"
        body = (
            "Today is a calm day in the sky. Use this time to focus on simple, "
            "grounded actions and gentle self-care."
        )

    affirmation = "I move through this day calmly and with intention."

    return DailyDigestText(
        date=day,
        locale=locale,
        length=length,
        title=title,
        body=body,
        affirmation=affirmation,
        disclaimer=DISCLAIMER_EN,
    )


def _extract_text_from_atom(atom, length: str) -> str:
    """
    Берём подходящий текст из атома в зависимости от желаемой длины:

    - для short: copy_short (если есть), иначе первый абзац body
    - для medium: copy_long (если есть), иначе первые 1-2 абзаца body, иначе copy_short
    - для long: copy_long, иначе body целиком, иначе copy_short

    Логика разбиения body по абзацам:
    - Абзацы разделяются двойным переносом строки "\n\n"
    - Для medium берём первые 2 абзаца (если body содержит >2 абзацев)
    - Для short берём первый абзац
    """
    base_body = getattr(atom, "body", None) or ""
    short = (atom.copy_short or "").strip()
    long_ = (atom.copy_long or "").strip()

    # Разбиваем body на абзацы
    paragraphs = []
    if base_body:
        paragraphs = [p.strip() for p in base_body.split("\n\n") if p.strip()]

    if length == "short":
        # Приоритет: copy_short > первый абзац body > body целиком
        if short:
            return short
        elif paragraphs:
            return paragraphs[0]
        else:
            return base_body

    elif length == "medium":
        # Приоритет: copy_long > первые 2 абзаца body > copy_short > body целиком
        if long_:
            return long_
        elif len(paragraphs) > 2:
            # Берём первые 2 абзаца
            return "\n\n".join(paragraphs[:2])
        elif paragraphs:
            # Если абзацев <=2, используем их все
            return "\n\n".join(paragraphs)
        elif short:
            return short
        else:
            return base_body

    else:  # length == "long"
        # Приоритет: copy_long > body целиком > copy_short
        if long_:
            return long_
        elif base_body:
            return base_body
        elif short:
            return short
        else:
            return ""


def _build_title_from_atom(atom) -> str:
    # Очень простой генератор заголовка: потом можно заменить на LLM.
    topic = getattr(atom, "topic_tag", None) or (atom.trigger or "").replace("_", " ")
    topic = topic.strip().title() if topic else "Your Daily Focus"
    return f"Today's focus: {topic}"


def _pick_affirmation(atoms: List[SelectedAtom]) -> Optional[str]:
    for sel in atoms:
        cta = (sel.atom.cta or "").strip()
        if cta:
            return cta
    # Fallback-утверждение
    return "Take a deep breath, center yourself, and trust your inner rhythm."


def _simple_render_body(chosen: List[SelectedAtom], length: str) -> str:
    """Склейка текстов атомов без LLM."""
    parts: List[str] = []
    for sel in chosen:
        text = _extract_text_from_atom(sel.atom, length)
        if text:
            parts.append(text.strip())
    return "\n\n".join(parts)


def render_daily_digest_from_atoms(
    atoms: List[SelectedAtom],
    day: date,
    user_profile: Optional[UserProfile] = None,
    *,
    length_override: Optional[str] = None,
    use_llm: bool = True,
) -> DailyDigestText:
    """
    Генерация текста дайджеста по выбранным атомам.

    При use_llm=True и подходящих условиях (2–6 атомов, RU) пробует LLM-улучшение;
    при промахе или ошибке — простой рендер из атомов.
    """
    locale = (user_profile.locale if user_profile else "en") or "en"
    length = _pick_effective_length(user_profile, length_override)

    logger.info(
        "[TEXT_GEN] render_daily_digest_from_atoms: received %d atoms, length=%s, locale=%s",
        len(atoms),
        length,
        locale,
    )

    if not atoms:
        logger.info("[TEXT_GEN] No atoms provided, returning fallback text")
        return _fallback_text(locale, length, day)

    chosen = atoms
    logger.info(
        "[TEXT_GEN] Using all %d atoms for rendering (length=%s)", len(chosen), length
    )

    for i, sel in enumerate(chosen, 1):
        logger.debug(
            "[TEXT_GEN] Atom %d: id=%d, trigger=%s, persona_tags=%s, score=%.2f",
            i,
            sel.atom.id,
            sel.atom.trigger,
            sel.atom.persona_tags,
            sel.score,
        )

    # Условие для LLM: включён флаг, 2–6 атомов, русская локаль
    should_use_llm = use_llm and 2 <= len(chosen) <= 6 and locale == "ru"
    body: str
    llm_usage: Optional[dict] = None
    render_variant = "simple"
    if should_use_llm:
        try:
            from common.config import get_settings
            from app.services.llm_service import LLMService, estimate_cost_usd

            llm = LLMService()
            result = llm.enhance_digest(chosen, [], user_profile, day)
            if result and result.body.strip():
                body = result.body.strip()
                render_variant = "llm"
                settings = get_settings()
                cost = estimate_cost_usd(result.prompt_tokens, result.completion_tokens)
                llm_usage = {
                    "model": settings.LLM_MODEL,
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "estimated_cost_usd": cost,
                    "cache_hit": result.cache_hit,
                }
                logger.info(
                    "[TEXT_GEN] Using LLM-enhanced body (%d chars, cache_hit=%s)",
                    len(body),
                    result.cache_hit,
                )
            else:
                body = _simple_render_body(chosen, length)
        except Exception as e:
            logger.warning("[TEXT_GEN] LLM enhance failed, fallback to simple: %s", e)
            body = _simple_render_body(chosen, length)
    else:
        body = _simple_render_body(chosen, length)

    if not body:
        logger.warning("[TEXT_GEN] No text extracted from atoms, returning fallback")
        return _fallback_text(locale, length, day)

    logger.info("[TEXT_GEN] Final digest: %d total chars", len(body))

    title = _build_title_from_atom(chosen[0].atom)
    affirmation = _pick_affirmation(chosen)

    return DailyDigestText(
        date=day,
        locale=locale,
        length=length,
        title=title,
        body=body,
        affirmation=affirmation,
        disclaimer=DISCLAIMER_EN,
        llm_usage=llm_usage,
        render_variant=render_variant,
    )
