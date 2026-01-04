# src/app/content_atoms_rag.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app import models
from app.repo import DEFAULT_LOCALE
from app.astro_core import ensure_daily_transits
from app.astro.global_events import compute_global_events, GlobalEvent

import sqlalchemy as sa
from app.astro.transit_service import compute_daily_digest_transits


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
    event: Optional[models.Event] = None


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


def _trigger_from_transit_aspect_details(details: dict) -> str:
    # mars_square_sun
    t = str(details.get("transit_body", "")).strip().lower()
    a = str(details.get("aspect", "")).strip().lower()
    n = str(details.get("natal_body", "")).strip().lower()
    return f"{t}_{a}_{n}".strip("_")


def event_to_atom_query(
    ev: models.Event,
    user_profile: Optional[UserProfile] = None,
) -> AtomQuery:
    details = ev.details or {}
    trigger = details.get("trigger") or _trigger_from_transit_aspect_details(details)

    persona_tags: List[str] = []
    if user_profile and user_profile.interests:
        persona_tags = _normalize_tags(user_profile.interests)

    locale = getattr(user_profile, "locale", "en")

    return AtomQuery(
        locale=locale,
        trigger=str(trigger).lower() if trigger else None,
        house_tags=[],
        persona_tags=persona_tags,
    )


def _strength_from_transit_details(details: dict) -> float:
    """
    Чем ближе к точному аспекту (orb -> 0), тем выше сила.
    Для digest (orb_max=2): strength ~ [0.5..1.0]
    Для strong (orb_max=1): strength ~ [0.6..1.0]
    """
    try:
        orb = float(details.get("orb_deg", 2.0))
    except (TypeError, ValueError):
        orb = 2.0

    bucket = (details.get("bucket") or "digest").lower()
    orb_max = 1.0 if bucket == "strong" else 2.0

    x = 1.0 - min(max(orb, 0.0), orb_max) / orb_max
    # не даём слишком низко падать
    floor = 0.6 if bucket == "strong" else 0.5
    return max(floor, x)


def _load_digest_transit_events_for_day(
    db: Session, user_id: int, day: date
) -> List[models.Event]:
    day_iso = day.isoformat()

    rows = (
        db.query(models.Event)
        .filter(
            models.Event.user_id == user_id,
            models.Event.kind == "transit_aspect",
            models.Event.details["bucket"].as_string() == "digest",
            models.Event.details["local_date"].as_string() == day_iso,
        )
        .order_by(models.Event.ts.asc())
        .all()
    )
    return rows


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
    Ищем кандидатов в content_atoms под AtomQuery.

    Правила:
    - сначала пробуем locale из запроса (query.locale, нормализуем в lower),
    - если ничего не нашли и locale != DEFAULT_LOCALE — пробуем DEFAULT_LOCALE,
    - внутри каждой локали:
        * если указан trigger — сначала ищем точное совпадение (case-insensitive),
        * если нет точных совпадений — берём все атомы этой локали.
    Возвращаем список (atom, sem_score), отсортированный по семантическому скору.
    """

    def _run_for_locale(locale: str) -> List[models.ContentAtom]:
        q = db.query(models.ContentAtom).filter(models.ContentAtom.locale == locale)

        if query.trigger:
            trig = query.trigger.lower()
            primary = q.filter(sa.func.lower(models.ContentAtom.trigger) == trig).all()
            if primary:
                return primary

        return q.all()

    # Нормализуем locale и делаем fallback на DEFAULT_LOCALE
    base_locale = (query.locale or DEFAULT_LOCALE).lower()

    candidates = _run_for_locale(base_locale)

    if not candidates and base_locale != DEFAULT_LOCALE:
        candidates = _run_for_locale(DEFAULT_LOCALE)

    # Семантический скор + сортировка
    scored: List[Tuple[models.ContentAtom, float]] = []
    for atom in candidates:
        sem_score = _semantic_score_atom_for_query(atom, query)
        scored.append((atom, sem_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:max_atoms]


def select_general_day_atoms(
    db: Session,
    user_profile: Optional[UserProfile],
    *,
    max_atoms: int = 2,
) -> List[SelectedAtom]:
    """
    Подбирает «общие» атомы дня (day_*) на случай тихого дня.

    Логика:
    - базово используем два универсальных тега:
        * day_general_balance
        * day_general_selfcare
    - если у пользователя есть интересы (profile.interests),
      то добавляем к ним более тематические теги:
        * work/career/job      → day_work_focus
        * money/finance        → day_money_focus
        * love/relations       → day_love_vibes
        * selfcare/health      → day_selfcare_nervous_system
      и даём им приоритет в выдаче;
    - если по локали ничего не нашли и locale != DEFAULT_LOCALE —
      пробуем DEFAULT_LOCALE;
    - возвращаем до max_atoms SelectedAtom без привязки к конкретному транзиту.
    """
    # Базовая локаль
    locale = (getattr(user_profile, "locale", None) or DEFAULT_LOCALE).lower()

    # База: два универсальных тега
    base_topic_tags = ["day_general_balance", "day_general_selfcare"]

    # Персонализированные теги по интересам пользователя
    topic_tags: List[str] = []
    interests: List[str] = []
    if user_profile and getattr(user_profile, "interests", None):
        interests = [
            str(x).strip().lower()
            for x in (user_profile.interests or [])
            if str(x).strip()
        ]

    interest_to_topic = {
        "work": "day_work_focus",
        "career": "day_work_focus",
        "job": "day_work_focus",
        "money": "day_money_focus",
        "finance": "day_money_focus",
        "finances": "day_money_focus",
        "love": "day_love_vibes",
        "relationship": "day_love_vibes",
        "relationships": "day_love_vibes",
        "selfcare": "day_selfcare_nervous_system",
        "health": "day_selfcare_nervous_system",
    }

    seen_topics: set[str] = set()
    # сначала — персонализированные теги
    for interest in interests:
        topic = interest_to_topic.get(interest)
        if topic and topic not in seen_topics:
            topic_tags.append(topic)
            seen_topics.add(topic)

    # затем — базовые теги (если их ещё нет)
    for t in base_topic_tags:
        if t not in seen_topics:
            topic_tags.append(t)
            seen_topics.add(t)

    def _run_for_locale(loc: str) -> List[models.ContentAtom]:
        q = db.query(models.ContentAtom).filter(
            models.ContentAtom.locale == loc,
            models.ContentAtom.topic_tag.in_(topic_tags),
        )

        # Упорядочиваем по приоритету topic_tags, затем по id
        when_clauses = [
            (models.ContentAtom.topic_tag == tag, idx)
            for idx, tag in enumerate(topic_tags)
        ]
        order_expr = sa.case(*when_clauses, else_=len(topic_tags))

        q = q.order_by(order_expr, models.ContentAtom.id.asc())
        return q.limit(max_atoms).all()

    atoms = _run_for_locale(locale)
    if not atoms and locale != DEFAULT_LOCALE:
        atoms = _run_for_locale(DEFAULT_LOCALE)

    result: List[SelectedAtom] = []
    for atom in atoms:
        result.append(
            SelectedAtom(
                atom=atom,
                # «Тихий» скор — используется только когда других атомов нет
                score=0.4,
                transit=None,
                global_event=None,
                event=None,
            )
        )
    return result


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

    # 1. Транзиты из events (precompute)
    transit_events = _load_digest_transit_events_for_day(db, user_id=user_id, day=day)

    # fallback: если precompute не запускался — считаем на лету (без записи в БД)
    if not transit_events:
        aspects = compute_daily_digest_transits(db, user_id=user_id, local_date=day)
        # превращаем в "как бы events"
        transit_events = []
        for a in aspects:
            details = {
                "bucket": "digest",
                "local_date": day.isoformat(),
                "tzid": getattr(user_profile, "timezone", None),
                "transit_body": a.transit_body,
                "natal_body": a.natal_body,
                "aspect": a.aspect,
                "orb_deg": a.orb_deg,
            }
            transit_events.append(
                models.Event(
                    user_id=user_id,
                    kind="transit_aspect",
                    ts=datetime.now(timezone.utc),
                    title="",
                    details=details,
                )
            )

    # 2. Глобальные события (stub-фазы Луны)
    global_events = compute_global_events(day, day)

    selected: List[SelectedAtom] = []

    # 3. Транзиты (events)
    for ev in transit_events:
        q = event_to_atom_query(ev, user_profile=user_profile)
        candidates = _find_atoms_for_query(db, q, max_atoms=2)

        details = ev.details or {}
        strength = _strength_from_transit_details(details)

        for atom, sem_score in candidates:
            total_score = sem_score + strength
            selected.append(
                SelectedAtom(
                    atom=atom,
                    score=total_score,
                    transit=None,
                    global_event=None,
                    event=ev,
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
