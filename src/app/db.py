# src/app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"client_encoding": "utf8"},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """
    FastAPI dependency для получения сессии БД.
    Используется в роутерах (birth_data, user_prefs, telegram и др.).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
