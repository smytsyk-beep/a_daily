from fastapi import APIRouter, Query
from typing import List, Dict, Any

from app.repo import session_scope, recent_events

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/recent")
def events_recent(limit: int = Query(20, ge=1, le=200)) -> List[Dict[str, Any]]:
    # берём последние события через контекст-менеджер сессии
    with session_scope() as db:
        evs = recent_events(db, limit=limit)

    # сериализация в простой JSON-вид
    return [
        {
            "id": e.id,
            "event": e.event_ref,
            "created_at": e.created_at.isoformat(),
            "payload": e.note if isinstance(e.note, dict) else e.note,  # note уже строка/JSON-строка
            "score": e.score,
        }
        for e in evs
    ]


"""
from fastapi import APIRouter, Query
from app.repo import get_session, recent_events
import json

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/recent")
def events_recent(limit: int = Query(20, ge=1, le=200)):
    with get_session() as db:
        rows = recent_events(db, limit=limit)
        out = []
        for r in rows:
            payload = None
            if r.note:
                try:
                    payload = json.loads(r.note)
                except Exception:
                    payload = {"raw_note": r.note}
            out.append({
                "id": r.id,
                "event": r.event_ref,  # ← используем event_ref
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "payload": payload,
                "score": r.score,
            })
return out
"""