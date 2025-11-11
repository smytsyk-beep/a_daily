from fastapi import FastAPI
from app.routes_health import router as health_router  # ABSOLUTE import

app = FastAPI(title="AstroDaily API")

@app.get("/", tags=["root"])
def root():
    return {"ok": True, "name": "AstroDaily", "version": "0.1.0"}

app.include_router(health_router)