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

import logging

logger = logging.getLogger(__name__)

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


# В сидах отношения часто помечены "love"; интерес пользователя — "relationships".
# При поиске атомов считаем их эквивалентными.
USER_INTEREST_TO_PERSONA: dict[str, list[str]] = {
    "relationships": ["relationships", "love"],
}


def _interests_to_query_personas(interests: Optional[Sequence[str]]) -> List[str]:
    """Превращает интересы пользователя в список тегов для запроса (с учётом love/relationships)."""
    if not interests:
        return []
    out: set[str] = set()
    for x in interests:
        s = str(x).strip().lower()
        if not s:
            continue
        out.add(s)
        if s in USER_INTEREST_TO_PERSONA:
            for alias in USER_INTEREST_TO_PERSONA[s]:
                out.add(alias)
    return sorted(out)


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
        persona_tags = _interests_to_query_personas(user_profile.interests)

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
        persona_tags = _interests_to_query_personas(user_profile.interests)

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
        persona_tags = _interests_to_query_personas(user_profile.interests)

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
    +0.7  — за каждое пересечение persona_tags (усилен для учёта интересов)
    +1.0  — бонус за покрытие всех интересов пользователя (coverage_ratio)
    +1.5  — эксклюзивный match (атом точно соответствует интересам пользователя)
    +0.2  — за каждое пересечение house_tags
    +0.5  — бонус за "general" тег (универсальный контент)
    """
    score = 0.0

    # 1) Совпадение триггера
    if atom.trigger and query.trigger and atom.trigger == query.trigger:
        score += 1.0

    # 2) Пересечение persona_tags (увеличен коэффициент с 0.3 до 0.7)
    atom_personas = set(_normalize_tags(atom.persona_tags))
    query_personas = set(query.persona_tags)

    if atom_personas and query_personas:
        matched_personas = atom_personas & query_personas
        matched_count = len(matched_personas)

        # Базовый score за совпадения
        score += 0.7 * matched_count

        # Бонус за coverage (чем больше интересов пользователя покрыто, тем лучше)
        total_user_interests = len(query_personas)
        if total_user_interests > 0:
            coverage_ratio = matched_count / total_user_interests
            score += 1.0 * coverage_ratio  # до +1.0 за полное покрытие

        # Эксклюзивный match: атом содержит ТОЛЬКО интересы пользователя (и "general")
        # Это означает, что атом идеально подходит для этого пользователя
        atom_personas_clean = atom_personas - {
            "general"
        }  # убираем "general" для проверки
        query_personas_clean = query_personas - {"general"}

        if query_personas_clean and atom_personas_clean:
            # Если атом содержит ТОЛЬКО интересы пользователя (без лишних тегов)
            if atom_personas_clean <= query_personas_clean:  # subset или equal
                score += 1.5  # сильный бонус за эксклюзивность

    # Бонус за "general" — универсальный контент, который подходит всем
    if "general" in atom_personas:
        score += 0.5

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
        * ПРИОРИТЕТ 1: атомы с совпадением trigger И persona_tags
        * ПРИОРИТЕТ 2: атомы с совпадением только trigger
        * ПРИОРИТЕТ 3: атомы с совпадением только persona_tags
        * ПРИОРИТЕТ 4: все атомы локали (fallback)
    Возвращаем список (atom, sem_score), отсортированный по семантическому скору.
    """

    def _run_for_locale(locale: str) -> List[models.ContentAtom]:
        base_q = db.query(models.ContentAtom).filter(
            models.ContentAtom.locale == locale
        )

        # Приоритет 1: trigger + persona_tags
        # Используем Python-фильтрацию для надёжности (JSONB оператор ?| проблематичен)
        if query.trigger and query.persona_tags:
            trig = query.trigger.lower()
            trigger_match = base_q.filter(
                sa.func.lower(models.ContentAtom.trigger) == trig
            ).all()

            if trigger_match:
                # Фильтруем по persona_tags в Python
                query_personas_set = set(query.persona_tags)
                filtered = []
                for atom in trigger_match:
                    atom_personas = set(_normalize_tags(atom.persona_tags))
                    if atom_personas & query_personas_set:
                        filtered.append(atom)

                if filtered:
                    logger.debug(
                        "[RAG] Found %d atoms with trigger=%s AND persona_tags overlap for locale=%s",
                        len(filtered),
                        query.trigger,
                        locale,
                    )
                    return filtered

        # Приоритет 2: только trigger
        if query.trigger:
            trig = query.trigger.lower()
            trigger_match = base_q.filter(
                sa.func.lower(models.ContentAtom.trigger) == trig
            ).all()
            if trigger_match:
                logger.debug(
                    "[RAG] Found %d atoms with trigger=%s for locale=%s",
                    len(trigger_match),
                    query.trigger,
                    locale,
                )
                return trigger_match

        # Приоритет 3: только persona_tags (если нет trigger match)
        if query.persona_tags:
            logger.debug("[RAG] Filtering by persona_tags in Python")
            all_atoms = base_q.all()
            persona_match = []
            query_personas_set = set(query.persona_tags)
            for atom in all_atoms:
                atom_personas = set(_normalize_tags(atom.persona_tags))
                if atom_personas & query_personas_set:
                    persona_match.append(atom)

            if persona_match:
                logger.debug(
                    "[RAG] Found %d atoms with persona_tags overlap for locale=%s",
                    len(persona_match),
                    locale,
                )
                return persona_match[: max_atoms * 2]

        # Приоритет 4: атомы с "general" persona_tag (исключаем test-атомы)
        # Сначала пробуем найти атомы с тегом "general"
        all_atoms = base_q.all()

        # Фильтруем: убираем test-атомы (ml_test_tag, test_*)
        filtered_atoms = []
        general_atoms = []

        for atom in all_atoms:
            # Пропускаем test-атомы
            topic = (atom.topic_tag or "").lower()
            trigger = (atom.trigger or "").lower()

            if "test" in topic or "test" in trigger:
                continue

            # Разделяем на "general" и остальные
            persona_tags = set(_normalize_tags(atom.persona_tags))
            if "general" in persona_tags:
                general_atoms.append(atom)
            else:
                filtered_atoms.append(atom)

        # Приоритет: сначала general, потом остальные
        result = general_atoms + filtered_atoms

        if result:
            logger.debug(
                "[RAG] Fallback: returning %d atoms (general: %d, other: %d) for locale=%s",
                len(result),
                len(general_atoms),
                len(filtered_atoms),
                locale,
            )
            return result[: max_atoms * 2]

        # Крайний fallback: если совсем ничего нет (даже test-атомов нет) — возвращаем пустой список
        logger.warning(
            "[RAG] No suitable atoms found for locale=%s (even after fallback)", locale
        )
        return []

    # Нормализуем locale и делаем fallback на DEFAULT_LOCALE
    base_locale = (query.locale or DEFAULT_LOCALE).lower()

    candidates = _run_for_locale(base_locale)

    if not candidates and base_locale != DEFAULT_LOCALE:
        logger.info(
            "[RAG] No atoms for locale=%s, trying DEFAULT_LOCALE=%s",
            base_locale,
            DEFAULT_LOCALE,
        )
        candidates = _run_for_locale(DEFAULT_LOCALE)

    # Семантический скор + сортировка
    scored: List[Tuple[models.ContentAtom, float]] = []
    for atom in candidates:
        sem_score = _semantic_score_atom_for_query(atom, query)
        scored.append((atom, sem_score))

    scored.sort(key=lambda x: x[1], reverse=True)

    logger.debug(
        "[RAG] Scored %d candidate atoms, returning top %d (max_score=%.2f)",
        len(scored),
        min(len(scored), max_atoms),
        scored[0][1] if scored else 0.0,
    )

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
        "learning": "day_general_balance",
        "creativity": "day_general_balance",
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
    logger.info(
        "[RAG] select_atoms_for_day START: user_id=%s day=%s max_total_atoms=%s",
        user_id,
        day,
        max_total_atoms,
    )

    if user_profile is None:
        user_profile = UserProfile(locale="en")

    # Логируем профиль пользователя для отладки
    logger.info(
        "[RAG] User profile: locale=%s, interests=%s, preferred_length=%s",
        user_profile.locale,
        user_profile.interests,
        user_profile.preferred_length,
    )

    # 1. Транзиты из events (precompute)
    transit_events = _load_digest_transit_events_for_day(db, user_id=user_id, day=day)

    logger.info(
        "[RAG] Loaded %d precomputed transit events from DB for user_id=%s day=%s",
        len(transit_events),
        user_id,
        day,
    )

    # fallback: если precompute не запускался — считаем на лету
    # и ОДНОВРЕМЕННО сохраняем события в БД, чтобы в следующий раз читать их как precompute
    if not transit_events:
        logger.info(
            "[RAG] No precomputed events found. Computing transit aspects on-the-fly for user_id=%s day=%s",
            user_id,
            day,
        )

        aspects = compute_daily_digest_transits(db, user_id=user_id, local_date=day)

        logger.info(
            "[RAG] Computed %d transit aspects from transit_service for user_id=%s day=%s",
            len(aspects),
            user_id,
            day,
        )

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

            ev = models.Event(
                user_id=user_id,
                kind="transit_aspect",
                ts=datetime.now(timezone.utc),
                title="",
                details=details,
            )

            # важное отличие: записываем в сессию
            db.add(ev)
            transit_events.append(ev)

        # ВАЖНО: коммитим события в БД, чтобы они сохранились для будущих вызовов
        try:
            db.commit()
            logger.info(
                "[RAG] Committed %d transit events to DB for user=%s day=%s",
                len(transit_events),
                user_id,
                day,
            )
        except Exception as e:
            logger.error(
                "[RAG] Failed to commit transit events: %s",
                e,
                exc_info=True,
            )
            # откат, чтобы не сломать сессию
            db.rollback()

    # 2. Глобальные события (stub-фазы Луны)
    global_events = compute_global_events(day, day)
    logger.info("[RAG] Found %d global events for day=%s", len(global_events), day)

    selected: List[SelectedAtom] = []

    # 3. Транзиты (events)
    for ev in transit_events:
        q = event_to_atom_query(ev, user_profile=user_profile)
        logger.debug(
            "[RAG] Query for event %d: trigger=%s, persona_tags=%s",
            ev.id,
            q.trigger,
            q.persona_tags,
        )

        candidates = _find_atoms_for_query(db, q, max_atoms=2)

        details = ev.details or {}
        strength = _strength_from_transit_details(details)

        logger.debug(
            "[RAG] Event %d: found %d candidate atoms, strength=%.2f",
            ev.id,
            len(candidates),
            strength,
        )

        for atom, sem_score in candidates:
            total_score = sem_score + strength
            logger.debug(
                "[RAG] Atom %d (trigger=%s, persona_tags=%s): sem_score=%.2f, strength=%.2f, total=%.2f",
                atom.id,
                atom.trigger,
                atom.persona_tags,
                sem_score,
                strength,
                total_score,
            )
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
        logger.debug(
            "[RAG] Query for global event %s: trigger=%s, persona_tags=%s",
            ge.kind,
            q.trigger,
            q.persona_tags,
        )

        candidates = _find_atoms_for_query(db, q, max_atoms=1)

        # для глобальных событий возьмём фиксированную силу 0.6
        strength = 0.6

        logger.debug(
            "[RAG] Global event %s: found %d candidate atoms, strength=%.2f",
            ge.kind,
            len(candidates),
            strength,
        )

        for atom, sem_score in candidates:
            total_score = sem_score + strength
            logger.debug(
                "[RAG] Atom %d for global event: sem_score=%.2f, total=%.2f",
                atom.id,
                sem_score,
                total_score,
            )
            selected.append(
                SelectedAtom(
                    atom=atom,
                    score=total_score,
                    transit=None,
                    global_event=ge,
                )
            )

    logger.info("[RAG] Total selected atoms before dedup: %d", len(selected))

    # 5. Дедуп по atom.id — оставляем вариант с максимальным score
    dedup: dict[int, SelectedAtom] = {}
    for item in selected:
        atom_id = item.atom.id
        existing = dedup.get(atom_id)
        if existing is None or item.score > existing.score:
            dedup[atom_id] = item

    final_atoms = list(dedup.values())
    logger.info("[RAG] After dedup: %d unique atoms", len(final_atoms))

    if not final_atoms:
        # нет подходящих атомов — день считается тихим,
        # text_generation вернёт спокойный дефолтный текст
        logger.info("[RAG] No atoms found, returning empty list (quiet day)")
        return []

    final_atoms.sort(key=lambda a: a.score, reverse=True)

    # 6. Логика "тихий день":
    # если даже лучший скор ниже порога — атомы не используем,
    # даём text_generation с дефолтным тихим текстом.
    max_score = final_atoms[0].score
    if max_score < quiet_day_threshold:
        logger.info(
            "[RAG] Quiet day detected: max_score=%.2f < threshold=%.2f for user_id=%s day=%s",
            max_score,
            quiet_day_threshold,
            user_id,
            day,
        )
        return []

    # Логируем топ атомы
    logger.info("[RAG] Top atoms (scores):")
    for i, atom in enumerate(final_atoms[:max_total_atoms], 1):
        logger.info(
            "  %d. Atom %d (trigger=%s, persona_tags=%s): score=%.2f",
            i,
            atom.atom.id,
            atom.atom.trigger,
            atom.atom.persona_tags,
            atom.score,
        )

    result = final_atoms[:max_total_atoms]
    logger.info(
        "[RAG] select_atoms_for_day DONE: returning %d atoms for user_id=%s day=%s (max_score=%.2f)",
        len(result),
        user_id,
        day,
        max_score,
    )

    return result
