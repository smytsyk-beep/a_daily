from typing import Optional, Union, Annotated
import json

from fastapi import APIRouter, Query

from app.deps import SessionDep
from app.repo import recent_events

router = APIRouter(prefix="/events", tags=["events"])

# ---------- Typed query params ----------

# Важно: В Query НЕ задаём default, только ограничения.
# Default задаётся в сигнатуре функции: limit: LimitParam = 20
LimitParam = Annotated[
    int,
    Query(
        ge=1,
        le=200,
        description="Max events to return (1–200)",
    ),
]

UserIdParam = Annotated[
    Optional[Union[str, int]],
    Query(
        description="Numeric user id or tg_user_id; omit to see all users",
    ),
]

EventRefParam = Annotated[
    Optional[str],
    Query(
        min_length=1,
        max_length=64,
        description="Event reference code to filter",
    ),
]


# ---------- Routes ----------


@router.get("/recent")
def events_recent(
    limit: LimitParam = 20,
    user_id: UserIdParam = None,
    event: EventRefParam = None,
    db: SessionDep = None,
):
    """
    Возвращает последние события из EventFeedback.

    - `limit` — 1..200, по умолчанию 20
    - `user_id` — numeric id или tg_user_id (строка) или None
    - `event` — фильтр по event_ref
    """
    items = recent_events(db, limit=limit, user_id=user_id, event=event)

    return [
        {
            "id": ev.id,
            "event": ev.event_ref,
            "created_at": ev.created_at.isoformat(),
            "payload": json.loads(ev.note) if ev.note else None,
            "score": ev.score,
        }
        for ev in items
    ]
