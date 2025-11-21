# src/app/main.py
from fastapi import FastAPI

from app.routes_health import router as health_router
from app.routes_db import router as db_router

from app.routes_orchestrator import router as orch_router
from app.routes_events import router as events_router
from app.routes_feedback import router as feedback_router
from app.routes_modules import (
    router as modules_router,
    public as modules_public_router,
)
from common.config import settings
from common.error_handling import setup_exception_handlers

app = FastAPI(title="AstroDaily API", debug=settings.DEBUG)
# app = FastAPI(title="AstroDaily API")

# регистрируем глобальный обработчик ошибок
setup_exception_handlers(app)


@app.get("/", tags=["root"])
def root():
    return {"ok": True, "name": "AstroDaily", "version": "0.1.0"}


# порядок тут не критичен
app.include_router(health_router)
app.include_router(db_router)
app.include_router(orch_router)
app.include_router(events_router)
app.include_router(feedback_router)
app.include_router(modules_router)
app.include_router(modules_public_router)
