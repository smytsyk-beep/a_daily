from typing import Optional, Union
from fastapi import APIRouter, Query
from app.deps import SessionDep
from app.repo import recent_events
import json

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent")
def events_recent(
    limit: int = Query(20, ge=1, le=200),
    user_id: Optional[Union[str, int]] = Query(None),
    event: Optional[str] = Query(None),
    db: SessionDep = None,
):
    items = recent_events(db, limit=limit, user_id=user_id, event=event)

    return [
        {
            "id": ev.id,
            "event": ev.event_ref,
            "created_at": ev.created_at.isoformat(),
            "payload": (json.loads(ev.note) if ev.note else None),
            "score": ev.score,
        }
        for ev in items
    ]
