# src/app/text_generation.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.content_atoms_rag import SelectedAtom, UserProfile
from app.astro.global_events import compute_global_events


DISCLAIMER_EN = (
    "This content is for entertainment and general inspiration only and "
    "is not medical, financial, or legal advice."
)


@dataclass
class DailyDigestText:
    """
    Результат генерации текста для дневного дайджеста.

    Это то, что потом будет уходить в /digest/daily и Telegram.
    """

    date: date
    locale: str
    length: str  # "short" | "medium" | "long"
    title: str
    body: str
    affirmation: Optional[str]
    disclaimer: str


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
    Fallback-текст на “тихий” день.

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
            "It’s a relatively calm day in the sky, so it’s a good moment "
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
    Берём подходящий текст из атома:
    - для short: предпочтительно copy_short, иначе copy_long/body;
    - для medium/long: copy_long, иначе copy_short/body.
    """
    base_body = getattr(atom, "body", None) or ""
    short = (atom.copy_short or "").strip()
    long_ = (atom.copy_long or "").strip() or base_body

    if length == "short":
        return short or long_ or base_body
    else:
        return long_ or short or base_body


def _build_title_from_atom(atom) -> str:
    # Очень простой генератор заголовка: потом можно заменить на LLM.
    topic = getattr(atom, "topic_tag", None) or (atom.trigger or "").replace("_", " ")
    topic = topic.strip().title() if topic else "Your Daily Focus"
    return f"Today’s focus: {topic}"


def _pick_affirmation(atoms: List[SelectedAtom]) -> Optional[str]:
    for sel in atoms:
        cta = (sel.atom.cta or "").strip()
        if cta:
            return cta
    # Fallback-утверждение
    return "Take a deep breath, center yourself, and trust your inner rhythm."


def render_daily_digest_from_atoms(
    atoms: List[SelectedAtom],
    day: date,
    user_profile: Optional[UserProfile] = None,
    *,
    length_override: Optional[str] = None,
) -> DailyDigestText:
    """
    Stub-генерация текста дайджеста на основе выбранных атомов.

    В будущем:
      - здесь будет вызов LLM с фактами (атома + транзиты + глобальные события);
      - тексты copy_short/copy_long станут "якорями" или примерами.

    Сейчас:
      - берём 1–3 атома (зависит от длины),
      - склеиваем их тексты,
      - добавляем дисклеймер и простую аффирмацию/ритуал;
      - если атомов нет (тихий день) — строим текст на базе фазы Луны.
    """
    locale = (user_profile.locale if user_profile else "en") or "en"
    length = _pick_effective_length(user_profile, length_override)

    if not atoms:
        # “Тихий день” — отдаём лунный fallback
        return _fallback_text(locale, length, day)

    # Сколько атомов используем
    if length == "short":
        max_atoms = 1
    elif length == "medium":
        max_atoms = 2
    else:  # long
        max_atoms = 3

    chosen = atoms[:max_atoms]

    # Тело текста
    parts: List[str] = []
    for sel in chosen:
        text = _extract_text_from_atom(sel.atom, length)
        if text:
            parts.append(text.strip())

    if not parts:
        # если по какой-то причине тексты пустые — тоже fallback по Луне
        return _fallback_text(locale, length, day)

    # Разделитель между абзацами
    body = "\n\n".join(parts)

    # Заголовок — по первому атому
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
    )
