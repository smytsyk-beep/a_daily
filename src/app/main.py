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
from app.routes_telegram import router as telegram_router
from app.routes_user_prefs import router as user_prefs_router
from app.routes_birth_data import router as birth_data_router
from app.routes_user_summary import router as user_summary_router
from app.routes_metrics import router as metrics_router

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
app.include_router(telegram_router)
app.include_router(user_prefs_router)
app.include_router(birth_data_router)
app.include_router(user_summary_router)
app.include_router(metrics_router)
