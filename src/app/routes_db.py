from fastapi import APIRouter
from sqlalchemy import text
from app.deps import SessionDep

router = APIRouter(tags=["db"])


@router.get("/db/health")
def db_health(db: SessionDep):
    # Простой ping к БД через сессию
    val = db.execute(text("SELECT 1")).scalar_one()
    return {"ok": True, "db": val}
