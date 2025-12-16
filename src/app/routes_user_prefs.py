# src/app/routes_user_prefs.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import models
from app.repo import session_scope

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_LENGTHS = ("short", "medium", "long")
ALLOWED_INTERESTS = {
    "general",
    "work",
    "love",
    "selfcare",
    "money",
    "creativity",
}


class UserPrefsOut(BaseModel):
    user_id: int
    locale: str
    interests: List[str]
    preferred_length: str
    delivery_enabled: bool
    time_local: Optional[str] = None


class UserPrefsUpdate(BaseModel):
    locale: Optional[str] = None
    interests: Optional[List[str]] = None
    preferred_length: Optional[str] = None  # short | medium | long
    delivery_enabled: Optional[bool] = None
    time_local: Optional[str] = None  # "HH:MM"


def _normalize_interests(raw) -> Optional[list[str]]:
    if raw is None:
        return None

    if not isinstance(raw, list):
        raw = [raw]

    cleaned: list[str] = []
    for x in raw:
        s = str(x).strip()
        if not s:
            continue
        # фильтруем по whitelilst, но не ломаемся, если пришло что-то новое
        if s in ALLOWED_INTERESTS:
            cleaned.append(s)

    if not cleaned:
        return None

    # убираем дубли, сохраняем порядок
    seen = set()
    result: list[str] = []
    for s in cleaned:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def _build_prefs_from_user(user: models.User) -> UserPrefsOut:
    locale = user.locale or "en"

    interests = user.digest_interests or ["general"]
    if not isinstance(interests, list):
        interests = [str(interests)]
    interests = [str(x).strip() for x in interests if str(x).strip()]
    if not interests:
        interests = ["general"]

    # легкая нормализация интересов (вдруг в БД есть старые значения)
    norm = _normalize_interests(interests)
    if norm is None:
        interests = ["general"]
    else:
        interests = norm

    preferred_length = user.digest_length_preference or "medium"
    if preferred_length not in ALLOWED_LENGTHS:
        preferred_length = "medium"

    delivery_enabled = (
        user.delivery_enabled if user.delivery_enabled is not None else True
    )

    # берём из delivery_time_local
    time_local = user.delivery_time_local

    return UserPrefsOut(
        user_id=user.id,
        locale=locale,
        interests=interests,
        preferred_length=preferred_length,
        delivery_enabled=delivery_enabled,
        time_local=time_local,
    )


@router.get("/{user_id}/prefs", response_model=UserPrefsOut)
def get_user_prefs(user_id: int) -> UserPrefsOut:
    """
    Вернёт настройки дайджестов для указанного user_id.

    Пока без аутентификации — предполагаем, что фронт знает id пользователя.
    """
    with session_scope() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return _build_prefs_from_user(user)


@router.patch("/{user_id}/prefs", response_model=UserPrefsOut)
def update_user_prefs(user_id: int, payload: UserPrefsUpdate) -> UserPrefsOut:
    """
    Частичное обновление настроек пользователя.
    Любое поле в теле запроса опционально.
    """
    with session_scope() as db:
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.locale is not None:
            user.locale = payload.locale

        if payload.interests is not None:
            norm = _normalize_interests(payload.interests)
            # Если ничего валидного не передали — не трогаем поле
            if norm is not None:
                user.digest_interests = norm

        if payload.preferred_length is not None:
            if payload.preferred_length not in ALLOWED_LENGTHS:
                raise HTTPException(
                    status_code=400,
                    detail=f"preferred_length must be one of {ALLOWED_LENGTHS}",
                )
            user.digest_length_preference = payload.preferred_length

        if payload.delivery_enabled is not None:
            user.delivery_enabled = payload.delivery_enabled

        if payload.time_local is not None:
            # здесь можно будет добавить строгую валидацию "HH:MM"
            user.delivery_time_local = payload.time_local

        db.commit()
        db.refresh(user)

        return _build_prefs_from_user(user)
