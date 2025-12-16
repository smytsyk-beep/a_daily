# src/app/routes_user_summary.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models
from app.repo import session_scope

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


def _get_user_by_ref(db: Session, user_ref: str) -> Optional[models.User]:
    """
    Ищем пользователя по:
      - numeric id  (если строка целиком состоит из цифр),
      - tg_user_id  (fallback).
    """
    user: Optional[models.User] = None

    # 1) Пробуем как числовой первичный ключ
    if user_ref.isdigit():
        user = db.query(models.User).filter(models.User.id == int(user_ref)).first()

    # 2) Если не нашли — ищем по tg_user_id
    if user is None:
        user = db.query(models.User).filter(models.User.tg_user_id == user_ref).first()

    return user


def _serialize_birth_data(bd: Optional[models.BirthData]) -> Dict[str, Any]:
    """
    Преобразуем BirthData в компактный JSON-блок.
    Если bd = None — возвращаем заглушку с has_birth_data = False.
    """
    if bd is None:
        return {"has_birth_data": False}

    return {
        "has_birth_data": True,
        "id": bd.id,
        "birth_date": bd.birth_date.isoformat() if bd.birth_date else None,
        "birth_time": bd.birth_time,
        "tz": bd.tz,
        "place": bd.place,
        "lat": bd.lat,
        "lon": bd.lon,
    }


def _serialize_entitlement(
    ent: Optional[models.Entitlement],
) -> Optional[Dict[str, Any]]:
    """
    Преобразуем Entitlement в JSON-блок.
    Если активной записи нет — возвращаем None.
    """
    if ent is None:
        return None

    def dt_to_iso(dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt is not None else None

    return {
        "id": ent.id,
        "plan": ent.plan,
        "active": bool(ent.active),
        "started_at": dt_to_iso(ent.started_at),
        "expires_at": dt_to_iso(ent.expires_at),
    }


@router.get("/summary")
def get_user_summary(
    user_ref: str = Query(
        ...,
        description="User id (int) или tg_user_id (строка) для поиска пользователя",
    ),
) -> Dict[str, Any]:
    """
    Агрегирующий эндпоинт для фронта.

    Возвращает:
      - блок user (основные поля + настройки доставки + age-gate/disclaimer),
      - блок birth_data (последняя запись по пользователю),
      - блок entitlement (текущий/последний план).

    Никаких side-effects (пользователь НЕ создаётся, если не найден).
    """
    with session_scope() as db:
        user = _get_user_by_ref(db, user_ref=user_ref)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found",
            )

        # последняя запись birth_data по user_id (если их несколько)
        birth_data = (
            db.query(models.BirthData)
            .filter(models.BirthData.user_id == user.id)
            .order_by(models.BirthData.id.desc())
            .first()
        )

        # самый "актуальный" entitlement — по expires_at (если есть)
        entitlement = (
            db.query(models.Entitlement)
            .filter(models.Entitlement.user_id == user.id)
            .order_by(models.Entitlement.expires_at.desc().nullslast())
            .first()
        )

        user_block: Dict[str, Any] = {
            "id": user.id,
            "tg_user_id": user.tg_user_id,
            "locale": user.locale,
            "timezone": user.timezone,
            "display_name": user.display_name,
            "digest_interests": user.digest_interests,
            "digest_length_preference": user.digest_length_preference,
            "delivery": {
                "time_local": user.delivery_time_local,
                "enabled": user.delivery_enabled,
                "quiet_mode": user.quiet_mode,
            },
            "age_gate": {
                "accepted": user.age_gate_accepted_at is not None,
                "accepted_at": user.age_gate_accepted_at,
            },
            "disclaimer": {
                "accepted": user.disclaimer_accepted_at is not None,
                "accepted_at": user.disclaimer_accepted_at,
            },
            "birthdata_consent": {
                "accepted": user.birthdata_consent_at is not None,
                "accepted_at": user.birthdata_consent_at,
            },
        }

        return {
            "user": user_block,
            "birth_data": _serialize_birth_data(birth_data),
            "entitlement": _serialize_entitlement(entitlement),
        }
