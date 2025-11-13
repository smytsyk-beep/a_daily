from fastapi import APIRouter
from app.repo import get_session, list_enabled_modules

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("")
def modules_list():
    with get_session() as db:
        rows = list_enabled_modules(db)
        return [
            {"module": r.module, "enabled": r.enabled, "config": r.config} for r in rows
        ]
