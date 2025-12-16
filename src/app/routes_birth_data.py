# src/app/routes_birth_data.py

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app import models
from app.db import get_db

router = APIRouter(
    prefix="/users",
    tags=["birth_data"],
)


class BirthDataIn(BaseModel):
    """
    Входная модель для сохранения данных рождения.
    """

    birth_date: date
    birth_time: Optional[str] = None  # "HH:MM" или None
    tz: Optional[str] = None
    place: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

    @field_validator("birth_time")
    @classmethod
    def validate_birth_time(cls, v: Optional[str]) -> Optional[str]:
        """Нормализуем и валидируем время в формате HH:MM."""
        if v is None or v == "":
            return None

        v = v.strip()
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("birth_time must be in HH:MM format")

        hh_str, mm_str = parts
        if not (hh_str.isdigit() and mm_str.isdigit()):
            raise ValueError("birth_time must be in HH:MM format")

        hh = int(hh_str)
        mm = int(mm_str)
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError("birth_time must be in HH:MM format")

        return f"{hh:02d}:{mm:02d}"


class BirthDataOut(BirthDataIn):
    """
    Выходная модель (то же самое, плюс id записи).
    """

    id: int


@router.get("/{user_id}/birth-data", response_model=BirthDataOut)
def get_birth_data(
    user_id: int,
    db: Session = Depends(get_db),
) -> BirthDataOut:
    """
    Возвращает последнюю запись BirthData для пользователя.

    Если данных нет — 404.
    """
    bd = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user_id)
        .order_by(models.BirthData.id.desc())
        .first()
    )

    if not bd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Birth data not found",
        )

    return BirthDataOut(
        id=bd.id,
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        tz=bd.tz,
        place=bd.place,
        lat=bd.lat,
        lon=bd.lon,
    )


@router.put("/{user_id}/birth-data", response_model=BirthDataOut)
def upsert_birth_data(
    user_id: int,
    payload: BirthDataIn,
    db: Session = Depends(get_db),
) -> BirthDataOut:
    """
    Создаёт или обновляет данные рождения для пользователя.

    Логика простая:
      - если запись есть — обновляем поля;
      - если нет — создаём новую.
    """
    bd = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user_id)
        .order_by(models.BirthData.id.desc())
        .first()
    )

    if bd is None:
        bd = models.BirthData(
            user_id=user_id,
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            tz=payload.tz,
            place=payload.place,
            lat=payload.lat,
            lon=payload.lon,
        )
        db.add(bd)
    else:
        bd.birth_date = payload.birth_date
        bd.birth_time = payload.birth_time
        bd.tz = payload.tz
        bd.place = payload.place
        bd.lat = payload.lat
        bd.lon = payload.lon

    db.commit()
    db.refresh(bd)

    return BirthDataOut(
        id=bd.id,
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        tz=bd.tz,
        place=bd.place,
        lat=bd.lat,
        lon=bd.lon,
    )
