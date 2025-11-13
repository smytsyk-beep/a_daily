from fastapi import APIRouter
from sqlalchemy import text
from app.db import engine

router = APIRouter(tags=["db"])


@router.get("/db/health")
def db_health():
    # простой ping к БД
    with engine.connect() as conn:
        val = conn.execute(text("SELECT 1")).scalar_one()
    return {"ok": True, "db": val}
