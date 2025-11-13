from fastapi import FastAPI
from app.routes_health import router as health_router  # ABSOLUTE import
from app.routes_db import router as db_router
from app.routes_modules import router as modules_router
from app.routes_orchestrator import router as orch_router
from app.routes_events import router as events_router
from app.routes_feedback import router as feedback_router

app = FastAPI(title="AstroDaily API")


@app.get("/", tags=["root"])
def root():
    return {"ok": True, "name": "AstroDaily", "version": "0.1.0"}


app.include_router(health_router)
app.include_router(db_router)
app.include_router(modules_router)
app.include_router(orch_router)
app.include_router(events_router)
app.include_router(feedback_router)
