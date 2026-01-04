from __future__ import annotations

from datetime import date
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.repo import session_scope, resolve_user_id, upsert_birth_data, get_birth_data

router = APIRouter(prefix="/birth", tags=["birth"])


class BirthDataIn(BaseModel):
    user_id: Optional[Union[int, str]] = Field(
        default=None, description="users.id или tg_user_id"
    )
    birth_date: date
    birth_time: Optional[str] = Field(default=None, description="HH:MM")
    tz: Optional[str] = Field(default=None, description="IANA tz, e.g. Europe/Kyiv")
    place: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class BirthDataOut(BaseModel):
    user_id: int
    birth_date: date
    birth_time: Optional[str]
    tz: Optional[str]
    place: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


@router.get("/{user_ref}", response_model=Optional[BirthDataOut])
def get_birth(user_ref: str):
    with session_scope() as db:
        uid = resolve_user_id(db, user_ref)
        bd = get_birth_data(db, uid)
        if not bd:
            return None

        return BirthDataOut(
            user_id=bd.user_id,
            birth_date=bd.birth_date,
            birth_time=bd.birth_time,
            tz=bd.tz,
            place=bd.place,
            lat=bd.lat,
            lon=bd.lon,
        )


@router.post("/upsert", response_model=BirthDataOut)
def upsert_birth(payload: BirthDataIn):
    with session_scope() as db:
        try:
            bd = upsert_birth_data(
                db=db,
                user_ref=payload.user_id,
                birth_date=payload.birth_date,
                birth_time=payload.birth_time,
                place=payload.place,
                lat=payload.lat,
                lon=payload.lon,
                tz=payload.tz,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        return BirthDataOut(
            user_id=bd.user_id,
            birth_date=bd.birth_date,
            birth_time=bd.birth_time,
            tz=bd.tz,
            place=bd.place,
            lat=bd.lat,
            lon=bd.lon,
        )
