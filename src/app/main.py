from __future__ import annotations

from fastapi import FastAPI

from common.config import Settings, get_settings
from common.error_handling import setup_exception_handlers


def root() -> dict[str, object]:
    return {"ok": True, "name": "AstroDaily", "version": "0.1.0"}


def register_public_pilot_routes(application: FastAPI) -> None:
    """Register the complete public HTTP surface for the production pilot."""

    from app.routes_health import router as health_router
    from app.routes_telegram import router as telegram_router

    application.include_router(health_router)
    application.include_router(telegram_router)


def register_non_production_routes(application: FastAPI) -> None:
    """Register development and test routes that are never public in production."""

    from app.routes_birth_data import router as birth_data_router
    from app.routes_db import router as db_router
    from app.routes_events import router as events_router
    from app.routes_feedback import router as feedback_router
    from app.routes_metrics import router as metrics_router
    from app.routes_modules import public as modules_public_router
    from app.routes_modules import router as modules_router
    from app.routes_orchestrator import router as orchestrator_router
    from app.routes_user_prefs import router as user_prefs_router
    from app.routes_user_summary import router as user_summary_router

    application.add_api_route("/", root, methods=["GET"], tags=["root"])
    application.include_router(db_router)
    application.include_router(orchestrator_router)
    application.include_router(events_router)
    application.include_router(feedback_router)
    application.include_router(modules_router)
    application.include_router(modules_public_router)
    application.include_router(user_prefs_router)
    application.include_router(birth_data_router)
    application.include_router(user_summary_router)
    application.include_router(metrics_router)


def create_app(runtime_settings: Settings | None = None) -> FastAPI:
    """Build an isolated application from one already validated environment."""

    resolved_settings = runtime_settings or get_settings()
    is_production = resolved_settings.APP_ENV == "prod"

    application = FastAPI(
        title="AstroDaily API",
        debug=False if is_production else resolved_settings.DEBUG,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )
    setup_exception_handlers(application)
    register_public_pilot_routes(application)

    if resolved_settings.APP_ENV in {"dev", "test"}:
        register_non_production_routes(application)

    return application


# Resolve and validate settings before any route module is imported.
settings = get_settings()
app = create_app(settings)
