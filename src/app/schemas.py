from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime


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
