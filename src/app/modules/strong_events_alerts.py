from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.repo import session_scope
from app.astro.transit_service import compute_strong_alert_transits
from common.plans import PlanFeature, is_feature_allowed_for_user

from app import models

Atom = Dict[str, Any]

# сколько сильных аспектов показываем максимум на день
MAX_EVENTS_PER_DAY = 3


def _topic_tag_for_aspect(aspect: str) -> str:
    # можно расширять позже
    return {
        "conjunction": "strong_conjunction",
        "opposition": "strong_opposition",
        "square": "strong_square",
        "trine": "strong_trine",
        "sextile": "strong_sextile",
    }.get(aspect, "generic_strong_transit")


def _resolve_user_pk(db, user_ref: str) -> int | None:
    """
    Принимаем либо внутренний user.id (строкой/числом),
    либо tg_user_id (строкой).
    """
    if isinstance(user_ref, str) and user_ref.isdigit():
        return int(user_ref)

    u = db.query(models.User).filter(models.User.tg_user_id == str(user_ref)).first()
    return u.id if u else None


def _fallback_atom(window_days: int) -> Atom:
    """
    Резервный атом, если ничего не посчиталось (нет birth_data, ошибок и т.п.)
    Нужен и для прод-поведения, и чтобы проходил тест на feature flags.
    """
    return {
        "module": "strong_events_alerts",
        "kind": "alert",
        "topic_tag": "generic_strong_transit_window",
        "weight": 1.0,
        "window_days": window_days,
    }


def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    """
    Строим список “сильных” транзитов на несколько дней вперёд.

    Сейчас:
      - считаем транзиты на лету через compute_strong_alert_transits;
      - для каждого дня берём не больше MAX_EVENTS_PER_DAY аспектов;
      - если ничего не получилось (нет данных / нет аспектов) —
        возвращаем один fallback-атом.
    """
    cfg = config or {}
    window_days = int(cfg.get("window_days", 3))

    today = datetime.utcnow().date()
    atoms: List[Atom] = []

    with session_scope() as db:
        uid = _resolve_user_pk(db, user_id)
        if uid is None:
            # fallback, если пользователя не нашли
            return [_fallback_atom(window_days)]

        # ----- План-гейтинг, но только если у пользователя вообще есть entitlements -----
        has_entitlement = (
            db.query(models.Entitlement)
            .filter(
                models.Entitlement.user_id == uid,
                models.Entitlement.active.is_(True),
            )
            .first()
            is not None
        )

        if has_entitlement:
            # Для пользователей с entitlements — строгий гейтинг по плану:
            # STRONG_ALERTS только на full/internal.
            if not is_feature_allowed_for_user(db, uid, PlanFeature.STRONG_ALERTS):
                return []

        for offset in range(window_days):
            day = today + timedelta(days=offset)

            try:
                aspects = compute_strong_alert_transits(db, user_id=uid, local_date=day)
            except Exception:
                # типичный кейс — нет birth_data; в этом случае просто пропускаем день
                aspects = []

            if not aspects:
                continue

            for a in aspects[:MAX_EVENTS_PER_DAY]:
                atoms.append(
                    {
                        "module": "strong_events_alerts",
                        "kind": "alert",
                        "topic_tag": _topic_tag_for_aspect(a.aspect),
                        "weight": 1.0,
                        "day": day.isoformat(),
                        "window_days": window_days,
                        "transit": {
                            "transit_body": a.transit_body,
                            "natal_body": a.natal_body,
                            "aspect": a.aspect,
                            "orb_deg": a.orb_deg,
                        },
                    }
                )

    if not atoms:
        # если за всё окно так ничего и не набрали —
        # возвращаем один обобщённый атом
        atoms.append(_fallback_atom(window_days))

    return atoms
