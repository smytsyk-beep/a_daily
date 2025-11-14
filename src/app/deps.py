from typing import Annotated, Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSessionDep = Annotated[Session, Depends(get_session)]
SessionDep = DBSessionDep  # alias для совместимости
