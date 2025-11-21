# src/app/schemas.py
from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, Field


class EventOut(BaseModel):
    id: int
    user_id: Optional[int]
    kind: str
    ts: datetime
    title: str
    details: Optional[dict[str, Any]] = None


class DigestDayOut(BaseModel):
    date: str
    events: List[EventOut] = Field(default_factory=list)


class StrongAlertsOut(BaseModel):
    ts: datetime
    count: int
    events: List[EventOut] = Field(default_factory=list)


class FeedbackIn(BaseModel):
    """
    Входная схема для /events/feedback.
    Чуть ужесточаем валидацию, но не ломаем существующий контракт.
    """

    event: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Ключ события (например, 'preview_rendered')",
    )
    # score опционален, но если есть — только 1..5
    score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Оценка 1..5 (опционально)",
    )
    # Небольшой лимит на длину текста, чтобы не заливали романы :)
    note: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Свободный текстовый комментарий пользователя",
    )
    # user_id как строка — чтобы можно было передавать и int, и tg-алиас
    user_id: Optional[str] = Field(
        default=None,
        description="user_id или tg_user_id; если не задано, можно логировать как system",
    )
