from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.SQLALCHEMY_ECHO,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
