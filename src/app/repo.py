from contextlib import contextmanager
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import ModuleRegistry

@contextmanager
def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Queries ---
def list_enabled_modules(db: Session) -> list[ModuleRegistry]:
    return db.query(ModuleRegistry).filter(ModuleRegistry.enabled.is_(True)).order_by(ModuleRegistry.module).all()