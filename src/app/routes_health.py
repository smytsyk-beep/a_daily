from fastapi import APIRouter
from common.config import settings  # ABSOLUTE import

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {
        "ok": True,
        "env": settings.APP_ENV,
        "name": settings.APP_NAME,
        "version": "0.1.0",
    }