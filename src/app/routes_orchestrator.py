from fastapi import APIRouter
from app.orchestrator import run_preview

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/preview")
def preview(user_id: str = "demo"):
    return run_preview(user_id)
