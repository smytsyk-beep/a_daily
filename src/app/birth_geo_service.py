# src/app/birth_geo_service.py
"""
Сервис для обработки birth data и геокодирования места рождения.

Использует унифицированный geocoder из app.services.geocoder.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app import models
from app.services.geocoder import get_geocoder_service, GeoResult
from app.services.timezone import tz_by_latlon
from common.config import get_settings


def _get_user_language(user: models.User) -> str:
    """Определяет язык пользователя для геокодирования"""
    if user.locale:
        return user.locale
    return "en"


def ensure_birthdata_geo_for_user(db: Session, user: models.User) -> None:
    """
    Гарантирует, что у BirthData для данного user есть lat/lon (и по возможности tz).

    Логика:
      1) Берём последнюю запись BirthData по user.id.
      2) Если lat/lon уже есть → ничего не делаем.
      3) Если place пустой → выходим.
      4) Через geocode_place(place) получаем lat/lon.
      5) При необходимости через tz_by_latlon(lat, lon) пытаемся получить tz.
      6) Сохраняем изменения в БД.

    ВАЖНО: user.timezone здесь НЕ трогаем — это отдельная настройка
    “таймзона доставки”, чтобы не смешивать смыслы.
    """
    birth: Optional[models.BirthData] = (
        db.query(models.BirthData)
        .filter(models.BirthData.user_id == user.id)
        .order_by(models.BirthData.id.desc())
        .first()
    )

    if not birth:
        logger.info(f"[GEO] No BirthData for user_id={user.id}")
        return

    if birth.lat is not None and birth.lon is not None:
        # Координаты уже есть — считаем, что всё ок.
        # (tz можем добавить отдельно, если очень нужно.)
        return

    place = birth.place or ""
    if not place:
        logger.info(f"[GEO] BirthData has empty place for user_id={user.id}")
        return

    # Используем унифицированный geocoder
    settings = get_settings()
    geocoder = get_geocoder_service(
        db=db,
        mode=settings.GEOCODER_MODE,
        nominatim_url=settings.NOMINATIM_BASE_URL,
        nominatim_timeout=settings.NOMINATIM_TIMEOUT_S,
        google_api_key=settings.GOOGLE_GEOCODING_API_KEY,
        google_timeout=settings.GOOGLE_GEOCODING_TIMEOUT_S,
        cache_ttl_days=settings.GEOCODER_CACHE_TTL_DAYS,
    )

    user_lang = _get_user_language(user)
    geo = geocoder.geocode(place, language=user_lang)

    if not geo:
        logger.warning(
            f"[GEO] Could not geocode birth place for user_id={user.id}, "
            f"place={place!r}"
        )
        return

    birth.lat = geo.lat
    birth.lon = geo.lon

    # tz — по возможности через timezonefinder
    if not birth.tz:
        tz = tz_by_latlon(geo.lat, geo.lon)
        if tz:
            birth.tz = tz

    db.add(birth)
    db.commit()
    db.refresh(birth)

    logger.info(
        f"[GEO] BirthData updated for user_id={user.id}: "
        f"lat={birth.lat}, lon={birth.lon}, tz={birth.tz}, "
        f"place={place!r}, provider={geo.provider}"
    )
