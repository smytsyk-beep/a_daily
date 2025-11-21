from typing import Annotated
from fastapi import APIRouter, Query
from app.orchestrator import run_preview

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

UserIdParam = Annotated[
    str,
    Query(
        min_length=1,
        max_length=64,
        description="Internal user id / tg_user_id / 'system'",
    ),
]


@router.get("/preview")
def orchestrator_preview(user_id: UserIdParam = "system"):
    return run_preview(user_id)
