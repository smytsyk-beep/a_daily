# src/app/services/llm_service.py
"""
Сервис для LLM-улучшения дайджеста с кэшированием и fallback.

Кэширование (уровень 2 после TODAY_CACHE в routes_telegram):
- In-memory LRU по ключу locale|length|day|hash(atom texts), max 500 записей.
- При cache hit токены=0, в llm_usage_log пишется cache_hit=True для метрик.

Стратегия:
1. Проверить кэш (in-memory).
2. Если нет — вызвать OpenAI.
3. При ошибке вернуть None — вызывающий код сделает простой рендер.
"""

from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Optional

from common.config import get_settings

from app.content_atoms_rag import SelectedAtom, UserProfile
from app.services.llm_prompts import (
    SYSTEM_PROMPT_RU,
    build_digest_prompt_ru,
)

logger = logging.getLogger(__name__)

# Цены USD за 1M tokens (OpenAI gpt-4o-mini)
OPENAI_INPUT_COST_PER_1M = 0.15
OPENAI_OUTPUT_COST_PER_1M = 0.60


@dataclass
class LLMResult:
    body: str
    prompt_tokens: int
    completion_tokens: int
    cache_hit: bool


def _extract_text_from_atom(atom, length: str) -> str:
    """Та же логика, что в text_generation: short/medium/long из body, copy_short, copy_long."""
    base_body = getattr(atom, "body", None) or ""
    short = (getattr(atom, "copy_short", None) or "").strip()
    long_ = (getattr(atom, "copy_long", None) or "").strip()
    paragraphs = (
        [p.strip() for p in base_body.split("\n\n") if p.strip()] if base_body else []
    )
    if length == "short":
        return short or (paragraphs[0] if paragraphs else base_body)
    if length == "medium":
        if long_:
            return long_
        if len(paragraphs) > 2:
            return "\n\n".join(paragraphs[:2])
        if paragraphs:
            return "\n\n".join(paragraphs)
        return short or base_body
    # long
    return long_ or base_body or short or ""


def _extract_texts_from_atoms(atoms: List[SelectedAtom], length: str) -> List[str]:
    """Достаёт тексты из атомов в порядке длины (short/medium/long)."""
    return [_extract_text_from_atom(sel.atom, length) for sel in atoms]


def _cache_key(locale: str, length: str, day: date, atom_texts: List[str]) -> str:
    raw = f"{locale}|{length}|{day.isoformat()}|" + "|".join(atom_texts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class LLMService:
    """
    Улучшение дайджеста через LLM с кэшем и fallback.

    Использование только при 2–6 атомах и включённом LLM_ENABLED.
    """

    def __init__(self, cache_max_entries: int = 500):
        self._cache: OrderedDict[str, tuple[str, datetime]] = OrderedDict()
        self._cache_max = cache_max_entries

    def enhance_digest(
        self,
        atoms: List[SelectedAtom],
        transits: List,  # не используется в промпте пока
        user_profile: Optional[UserProfile],
        day: date,
    ) -> Optional[LLMResult]:
        """
        Возвращает улучшенный текст дайджеста или None при ошибке/отключении.
        """
        settings = get_settings()
        if not settings.LLM_ENABLED or not settings.OPENAI_API_KEY:
            logger.debug("[LLM] Disabled or no API key, skip enhance")
            return None

        locale = (user_profile.locale if user_profile else "en") or "en"
        length = (
            user_profile.preferred_length if user_profile else "medium"
        ) or "medium"
        interests = list(user_profile.interests) if user_profile else []

        if locale != "ru":
            logger.debug("[LLM] Only RU prompts implemented, skip")
            return None

        atom_texts = _extract_texts_from_atoms(atoms, length)
        if not any(t.strip() for t in atom_texts):
            return None

        key = _cache_key(locale, length, day, atom_texts)
        now = datetime.now(timezone.utc)
        if key in self._cache:
            body, _ = self._cache[key]
            self._cache.move_to_end(key)
            logger.info("[LLM] Cache hit for digest enhance")
            return LLMResult(
                body=body,
                prompt_tokens=0,
                completion_tokens=0,
                cache_hit=True,
            )

        try:
            response = self._call_openai(
                system=SYSTEM_PROMPT_RU,
                user_prompt=build_digest_prompt_ru(atom_texts, length, interests),
                max_tokens=800,
            )
        except Exception as e:
            logger.warning("[LLM] OpenAI call failed: %s", e, exc_info=True)
            return None

        if not response or not response.get("body"):
            return None

        body = response["body"].strip()
        prompt_tokens = response.get("prompt_tokens", 0)
        completion_tokens = response.get("completion_tokens", 0)

        # Кэш
        while len(self._cache) >= self._cache_max:
            self._cache.popitem(last=False)
        self._cache[key] = (body, now)

        return LLMResult(
            body=body,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_hit=False,
        )

    def _call_openai(
        self,
        system: str,
        user_prompt: str,
        max_tokens: int = 800,
    ) -> Optional[dict]:
        """Вызов OpenAI Chat Completions. Возвращает {body, prompt_tokens, completion_tokens} или None."""
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("[LLM] openai package not installed")
            return None

        settings = get_settings()
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )

        choice = resp.choices[0] if resp.choices else None
        if not choice or not choice.message or not choice.message.content:
            return None

        usage = resp.usage
        return {
            "body": choice.message.content,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        }


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Оценка стоимости в USD для gpt-4o-mini."""
    return (
        prompt_tokens * OPENAI_INPUT_COST_PER_1M / 1_000_000
        + completion_tokens * OPENAI_OUTPUT_COST_PER_1M / 1_000_000
    )
