# src/app/content_atoms_rag.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app import models
from app.astro_core import ensure_daily_transits
from app.astro.global_events import compute_global_events, GlobalEvent


# ================== Вспомогательные структуры ==================


@dataclass
class UserProfile:
    """
    Минимальный профиль пользователя для подбора контента.

    interests: теги вроде ["work", "love", "selfcare", "money", "creativity"].
    preferred_length: "short" | "medium" | "long".
    delivery_time_local: опциональное локальное время отправки дайджеста ("HH:MM").
    """

    locale: str = "en"
    interests: List[str] = field(default_factory=list)
    preferred_length: str = "medium"
    delivery_time_local: str | None = None


@dataclass
class AtomQuery:
    """
    Нормализованный запрос к контент-атомам:
    - trigger: формальный ключ события (например "Mercury_trine_Moon"),
    - house_tags/persona_tags: фильтры по домам и темам.
    """

    locale: str
    trigger: Optional[str]
    house_tags: List[str] = field(default_factory=list)
    persona_tags: List[str] = field(default_factory=list)


@dataclass
class SelectedAtom:
    """
    Результат подбора: сам атом + контекст, в связи с чем он выбран.

    score — итоговый скор (семантика + сила события).
    """

    atom: models.ContentAtom
    score: float
    transit: Optional[models.TransitEvent] = None
    global_event: Optional[GlobalEvent] = None


# ================== Маппинг событий в запросы ==================


def _normalize_tags(raw: Optional[Sequence[str]]) -> List[str]:
    if not raw:
        return []
    return sorted({str(x).strip() for x in raw if str(x).strip()})


def transit_to_atom_query(
    transit: models.TransitEvent,
    user_profile: Optional[UserProfile] = None,
) -> AtomQuery:
    """
    Переводит TransitEvent в запрос к контент-атомам.

    Сейчас опираемся на payload:
      - trigger: payload["trigger"] или kind,
      - house_tags: payload["house_tags"] / ["houses"],
      - persona_tags: payload["persona_tags"] или интересы пользователя.
    """
    payload = transit.payload or {}

    trigger = payload.get("trigger") or transit.kind

    house_tags = _normalize_tags(payload.get("house_tags") or payload.get("houses"))
    persona_tags = _normalize_tags(payload.get("persona_tags"))

    if not persona_tags and user_profile and user_profile.interests:
        persona_tags = _normalize_tags(user_profile.interests)

    locale = getattr(user_profile, "locale", "en")

    return AtomQuery(
        locale=locale,
        trigger=trigger,
        house_tags=house_tags,
        persona_tags=persona_tags,
    )


def global_event_to_atom_query(
    ev: GlobalEvent,
    user_profile: Optional[UserProfile] = None,
) -> AtomQuery:
    """
    Переводит GlobalEvent (фаза Луны / ингрессия / ретроградность)
    в запрос к контент-атомам.

    Конвенция: trigger = f"global_{ev.kind}", например "global_moon_phase".
    """
    trigger = f"global_{ev.kind}"

    persona_tags: List[str] = []
    if user_profile and user_profile.interests:
        persona_tags = _normalize_tags(user_profile.interests)

    locale = getattr(user_profile, "locale", "en")

    return AtomQuery(
        locale=locale,
        trigger=trigger,
        house_tags=[],
        persona_tags=persona_tags,
    )


# ================== Поиск и скоринг атомов ==================


def _semantic_score_atom_for_query(
    atom: models.ContentAtom,
    query: AtomQuery,
) -> float:
    """
    Чисто семантический скор по совпадению триггера и тегов.

    +1.0  — если совпал trigger
    +0.3  — за каждое пересечение persona_tags
    +0.2  — за каждое пересечение house_tags
    """
    score = 0.0

    # 1) Совпадение триггера
    if atom.trigger and query.trigger and atom.trigger == query.trigger:
        score += 1.0

    # 2) Пересечение persona_tags
    atom_personas = set(_normalize_tags(atom.persona_tags))
    query_personas = set(query.persona_tags)
    if atom_personas and query_personas:
        score += 0.3 * len(atom_personas & query_personas)

    # 3) Пересечение house_tags
    atom_houses = set(_normalize_tags(atom.house_tags))
    query_houses = set(query.house_tags)
    if atom_houses and query_houses:
        score += 0.2 * len(atom_houses & query_houses)

    return score


def _find_atoms_for_query(
    db: Session,
    query: AtomQuery,
    max_atoms: int = 3,
) -> List[Tuple[models.ContentAtom, float]]:
    """
    Ищем кандидатов в content_atoms под конкретный AtomQuery.

    Возвращаем список (atom, semantic_score) длиной до max_atoms.
    """
    q = db.query(models.ContentAtom).filter(models.ContentAtom.locale == query.locale)

    primary_candidates = []
    if query.trigger:
        primary_candidates = q.filter(models.ContentAtom.trigger == query.trigger).all()

    candidates = primary_candidates or q.all()

    scored: List[Tuple[models.ContentAtom, float]] = []
    for atom in candidates:
        s = _semantic_score_atom_for_query(atom, query)
        scored.append((atom, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:max_atoms]


# ================== Главный RAG-сервис ==================


def select_atoms_for_day(
    db: Session,
    user_id: int,
    day: date,
    user_profile: Optional[UserProfile] = None,
    *,
    max_total_atoms: int = 4,
    quiet_day_threshold: float = 0.5,
) -> List[SelectedAtom]:
    """
    Главный сервис RAG-слоя.

    Делает:
      1) ensure_daily_transits(...) — транзиты на день;
      2) compute_global_events(...) — глобальные события (пока фазы Луны);
      3) строит AtomQuery для каждого события;
      4) подбирает атомы с учётом семантики и силы события;
      5) ранжирует и применяет "тихий день", если всё слишком слабо.

    Итоговый score включает:
      - семантический скор,
      - strength события (если передан в payload["strength"]).
    """
    if user_profile is None:
        user_profile = UserProfile(locale="en")

    # 1. Транзиты (stub/реальные)
    transits = ensure_daily_transits(db, user_ref=user_id, day=day)

    # 2. Глобальные события (stub-фазы Луны)
    global_events = compute_global_events(day, day)

    selected: List[SelectedAtom] = []

    # 3. Транзиты
    for tr in transits:
        q = transit_to_atom_query(tr, user_profile=user_profile)
        candidates = _find_atoms_for_query(db, q, max_atoms=2)

        # сила события: по payload["strength"], по умолчанию 0.5
        strength = 0.5
        if tr.payload and isinstance(tr.payload, dict):
            try:
                strength = float(tr.payload.get("strength", strength))
            except (TypeError, ValueError):
                pass

        for atom, sem_score in candidates:
            total_score = sem_score + strength
            selected.append(
                SelectedAtom(
                    atom=atom,
                    score=total_score,
                    transit=tr,
                    global_event=None,
                )
            )

    # 4. Глобальные события
    for ge in global_events:
        q = global_event_to_atom_query(ge, user_profile=user_profile)
        candidates = _find_atoms_for_query(db, q, max_atoms=1)

        # для глобальных событий возьмём фиксированную силу 0.6
        strength = 0.6

        for atom, sem_score in candidates:
            total_score = sem_score + strength
            selected.append(
                SelectedAtom(
                    atom=atom,
                    score=total_score,
                    transit=None,
                    global_event=ge,
                )
            )

    # 5. Дедуп по atom.id — оставляем вариант с максимальным score
    dedup: dict[int, SelectedAtom] = {}
    for item in selected:
        atom_id = item.atom.id
        existing = dedup.get(atom_id)
        if existing is None or item.score > existing.score:
            dedup[atom_id] = item

    final_atoms = list(dedup.values())
    if not final_atoms:
        # нет подходящих атомов — день считается тихим,
        # text_generation вернёт спокойный дефолтный текст
        return []

    final_atoms.sort(key=lambda a: a.score, reverse=True)

    # 6. Логика "тихий день":
    # если даже лучший скор ниже порога — атомы не используем,
    # даём text_generation с дефолтным тихим текстом.
    max_score = final_atoms[0].score
    if max_score < quiet_day_threshold:
        return []

    return final_atoms[:max_total_atoms]
