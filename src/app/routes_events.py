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