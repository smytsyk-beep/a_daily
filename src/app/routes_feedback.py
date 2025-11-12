from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, Union
from sqlalchemy.orm import Session

from app.repo import get_db, log_event

router = APIRouter(prefix="/events", tags=["events"])

class FeedbackIn(BaseModel):
    user_id: Optional[Union[str, int]] = Field(
        None, description="int/число-строка -> users.id, иначе tg_user_id"
    )
    event_id: Optional[int] = Field(
        None, description="связанный event (если есть)"
    )
    score: int = Field(..., ge=1, le=5)
    note: Optional[str] = None

@router.post("/feedback")
def post_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    ev = log_event(
        db,
        event="feedback",
        user_id=payload.user_id,
        score=payload.score,
        payload={"event_id": payload.event_id, "note": payload.note},
    )
    return {"ok": True, "event_id": ev.id}
