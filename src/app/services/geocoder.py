# src/app/services/geocoder.py
"""
Унифицированный геокодер с поддержкой множественных провайдеров.

Архитектура:
- Provider Pattern для легкого переключения между Nominatim/Google/Self-hosted
- Агрессивное кеширование в БД (TTL ~10 лет, города не меняются)
- Chain mode: Nominatim → Google → Hardcoded fallback
- Нормализация ключей для максимального переиспользования cache

Использование:
    from app.services.geocoder import get_geocoder_service

    geocoder = get_geocoder_service(db, mode="chain")
    result = geocoder.geocode("Киев, Украина", language="ru")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.models import GeocodeCache


@dataclass
class GeoResult:
    """
    Унифицированный результат геокодинга.

    Attributes:
        lat: широта (decimal degrees)
        lon: долгота (decimal degrees)
        display_name: человекочитаемое имя места (для UI/логов)
        provider: источник данных ("cache" | "nominatim" | "google" | "hardcoded")
    """

    lat: float
    lon: float
    display_name: str
    provider: str


# ============================================================================
# Нормализация и утилиты
# ============================================================================


def _normalize_place(place: str) -> str:
    """
    Нормализация строки места для cache key.

    Цель: максимальное переиспользование cache.
    "Киев" = "Kiev" = "киев" = "KIEV" = "Киев, Украина"

    Правила:
    - lowercase
    - убираем запятые, лишние пробелы
    - ё → е (для русского)
    - удаляем точки в аббревиатурах (U.S.A. → usa)
    """
    s = (place or "").strip().lower()

    # Русская нормализация
    s = s.replace("ё", "е")

    # Удаляем пунктуацию (кроме дефисов внутри слов)
    s = s.replace(",", " ").replace(".", " ").replace(";", " ")

    # Схлопываем множественные пробелы
    parts = [p for p in s.split() if p]
    # Канонизация вариантов написания (единый ключ кеша: Kiev = Kyiv)
    parts = ["kyiv" if p == "kiev" else p for p in parts]
    return " ".join(parts)


# ============================================================================
# Hardcoded fallback (для CI/offline/популярных городов)
# ============================================================================

# Минимальный словарь популярных городов для fallback.
# Используется только если Nominatim и Google недоступны.
# Покрывает ~80% пользователей проекта (СНГ + основные мировые города).
FALLBACK_PLACES = {
    # === Украина ===
    "kyiv": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "kiev": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "киев": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "київ": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "kharkiv": (49.9935, 36.2304, "Kharkiv, Ukraine"),
    "харьков": (49.9935, 36.2304, "Kharkiv, Ukraine"),
    "харків": (49.9935, 36.2304, "Kharkiv, Ukraine"),
    "odesa": (46.4825, 30.7233, "Odesa, Ukraine"),
    "odessa": (46.4825, 30.7233, "Odesa, Ukraine"),
    "одесса": (46.4825, 30.7233, "Odesa, Ukraine"),
    "одеса": (46.4825, 30.7233, "Odesa, Ukraine"),
    "lviv": (49.8397, 24.0297, "Lviv, Ukraine"),
    "львов": (49.8397, 24.0297, "Lviv, Ukraine"),
    "львів": (49.8397, 24.0297, "Lviv, Ukraine"),
    # === Россия ===
    "moscow": (55.7558, 37.6173, "Moscow, Russia"),
    "москва": (55.7558, 37.6173, "Moscow, Russia"),
    "saint petersburg": (59.9343, 30.3351, "Saint Petersburg, Russia"),
    "санкт-петербург": (59.9343, 30.3351, "Saint Petersburg, Russia"),
    "питер": (59.9343, 30.3351, "Saint Petersburg, Russia"),
    "petersburg": (59.9343, 30.3351, "Saint Petersburg, Russia"),
    # === Беларусь ===
    "minsk": (53.9045, 27.5615, "Minsk, Belarus"),
    "минск": (53.9045, 27.5615, "Minsk, Belarus"),
    # === Казахстан ===
    "almaty": (43.2220, 76.8512, "Almaty, Kazakhstan"),
    "алматы": (43.2220, 76.8512, "Almaty, Kazakhstan"),
    # === Молдова ===
    "chisinau": (47.0105, 28.8638, "Chisinau, Moldova"),
    "кишинев": (47.0105, 28.8638, "Chisinau, Moldova"),
    # === США ===
    "new york": (40.7128, -74.0060, "New York, USA"),
    "нью-йорк": (40.7128, -74.0060, "New York, USA"),
    "nyc": (40.7128, -74.0060, "New York, USA"),
    "los angeles": (34.0522, -118.2437, "Los Angeles, USA"),
    "лос-анджелес": (34.0522, -118.2437, "Los Angeles, USA"),
    "la": (34.0522, -118.2437, "Los Angeles, USA"),
    # === Великобритания ===
    "london": (51.5074, -0.1278, "London, UK"),
    "лондон": (51.5074, -0.1278, "London, UK"),
    # === Турция ===
    "istanbul": (41.0082, 28.9784, "Istanbul, Turkey"),
    "стамбул": (41.0082, 28.9784, "Istanbul, Turkey"),
    # === Испания ===
    "madrid": (40.4168, -3.7038, "Madrid, Spain"),
    "мадрид": (40.4168, -3.7038, "Madrid, Spain"),
    "barcelona": (41.3874, 2.1686, "Barcelona, Spain"),
    "барселона": (41.3874, 2.1686, "Barcelona, Spain"),
    # === Страны (fallback на столицу) ===
    "ukraine": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "украина": (50.4501, 30.5234, "Kyiv, Ukraine"),
    "russia": (55.7558, 37.6173, "Moscow, Russia"),
    "россия": (55.7558, 37.6173, "Moscow, Russia"),
    "usa": (40.7128, -74.0060, "New York, USA"),
    "united states": (40.7128, -74.0060, "New York, USA"),
    "сша": (40.7128, -74.0060, "New York, USA"),
    "belarus": (53.9045, 27.5615, "Minsk, Belarus"),
    "беларусь": (53.9045, 27.5615, "Minsk, Belarus"),
    "spain": (40.4168, -3.7038, "Madrid, Spain"),
    "испания": (40.4168, -3.7038, "Madrid, Spain"),
    "turkey": (41.0082, 28.9784, "Istanbul, Turkey"),
    "турция": (41.0082, 28.9784, "Istanbul, Turkey"),
}


def _geocode_hardcoded(place: str) -> Optional[GeoResult]:
    """
    Fallback геокодер через hardcoded словарь.

    Используется только если:
    - Nominatim недоступен
    - Google недоступен или не настроен
    - CI/тесты (offline)
    """
    norm = _normalize_place(place)

    # 1. Прямое совпадение
    if norm in FALLBACK_PLACES:
        lat, lon, name = FALLBACK_PLACES[norm]
        # #region agent log
        try:
            import json

            with open("debug-e96797.log", "a", encoding="utf-8") as _f:
                _f.write(
                    json.dumps(
                        {
                            "sessionId": "e96797",
                            "hypothesisId": "A",
                            "location": "geocoder._geocode_hardcoded",
                            "message": "hardcoded result",
                            "data": {
                                "place": place,
                                "norm": norm,
                                "branch": "direct",
                                "lat": lat,
                                "lon": lon,
                                "lat_repr": repr(lat),
                                "lon_repr": repr(lon),
                            },
                            "timestamp": __import__("time").time() * 1000,
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion
        return GeoResult(lat, lon, name, "hardcoded")

    # 2. Поиск подстроки (для "Киев, Украина" → находим "киев")
    for key, (lat, lon, name) in FALLBACK_PLACES.items():
        if key in norm:
            # #region agent log
            try:
                import json

                with open("debug-e96797.log", "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "sessionId": "e96797",
                                "hypothesisId": "A",
                                "location": "geocoder._geocode_hardcoded",
                                "message": "hardcoded result",
                                "data": {
                                    "place": place,
                                    "norm": norm,
                                    "branch": "substring",
                                    "matched_key": key,
                                    "lat": lat,
                                    "lon": lon,
                                    "lat_repr": repr(lat),
                                    "lon_repr": repr(lon),
                                },
                                "timestamp": __import__("time").time() * 1000,
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion
            return GeoResult(lat, lon, name, "hardcoded")

    # 3. Пробуем взять последнее слово как страну
    tokens = norm.split()
    if tokens:
        last = tokens[-1]
        if last in FALLBACK_PLACES:
            lat, lon, name = FALLBACK_PLACES[last]
            # #region agent log
            try:
                import json

                with open("debug-e96797.log", "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "sessionId": "e96797",
                                "hypothesisId": "A",
                                "location": "geocoder._geocode_hardcoded",
                                "message": "hardcoded result",
                                "data": {
                                    "place": place,
                                    "norm": norm,
                                    "branch": "last",
                                    "lat": lat,
                                    "lon": lon,
                                    "lat_repr": repr(lat),
                                    "lon_repr": repr(lon),
                                },
                                "timestamp": __import__("time").time() * 1000,
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion
            return GeoResult(lat, lon, name, "hardcoded")
    return None


# ============================================================================
# Abstract Provider Interface
# ============================================================================


class GeocoderProvider(ABC):
    """
    Абстрактный провайдер геокодинга.

    Каждый конкретный провайдер (Nominatim, Google, etc.) реализует этот интерфейс.
    """

    @abstractmethod
    def geocode(self, place: str, language: str = "en") -> Optional[GeoResult]:
        """
        Геокодирование места → координаты.

        Args:
            place: строка места ("Киев, Украина", "New York, USA")
            language: код языка для мультиязычных результатов (ISO 639-1: en/ru/es/uk)

        Returns:
            GeoResult или None если не удалось геокодировать
        """
        pass


# ============================================================================
# Nominatim Provider (OSM, бесплатный)
# ============================================================================


class NominatimProvider(GeocoderProvider):
    """
    Провайдер на базе Nominatim (OpenStreetMap).

    Особенности:
    - Бесплатный
    - Поддержка мультиязычных запросов (accept-language header)
    - Лимит: 1 req/sec для публичного API (не проблема с cache)
    - Можно использовать self-hosted instance (без лимитов)
    """

    def __init__(self, base_url: str, timeout: int = 5):
        """
        Args:
            base_url: URL Nominatim instance
                - Публичный: "https://nominatim.openstreetmap.org"
                - Self-hosted: "http://nominatim:8080"
            timeout: таймаут запроса в секундах
        """
        self.base_url = base_url
        self.timeout = timeout
        self._geolocator = None

    def _get_geolocator(self):
        """Lazy initialization geopy Nominatim"""
        if self._geolocator is None:
            try:
                from geopy.geocoders import Nominatim

                self._geolocator = Nominatim(
                    user_agent="astrodaily/1.0",
                    domain=self.base_url.replace("https://", "").replace("http://", ""),
                    scheme=self.base_url.split("://")[0],
                    timeout=self.timeout,
                )
            except ImportError:
                logger.warning("geopy not installed, Nominatim provider disabled")
                return None
        return self._geolocator

    def geocode(self, place: str, language: str = "en") -> Optional[GeoResult]:
        """Геокодирование через Nominatim API"""
        geolocator = self._get_geolocator()
        if not geolocator:
            return None

        try:
            # accept-language для мультиязычных результатов
            location = geolocator.geocode(
                place, language=language, exactly_one=True, addressdetails=True
            )

            if not location:
                logger.debug(f"[Nominatim] Place not found: {place}")
                return None

            logger.info(f"[Nominatim] Geocoded: {place} → {location.address}")

            return GeoResult(
                lat=location.latitude,
                lon=location.longitude,
                display_name=location.address,
                provider="nominatim",
            )

        except Exception as e:
            logger.warning(f"[Nominatim] Error geocoding {place}: {e}")
            return None


# ============================================================================
# Google Provider (платный, fallback)
# ============================================================================


class GoogleProvider(GeocoderProvider):
    """
    Провайдер на базе Google Geocoding API.

    Особенности:
    - Платный ($5 за 1000 запросов после 200 бесплатных/месяц)
    - Самая точная база данных
    - Быстрые ответы
    - Хорошо работает с экзотическими адресами

    Рекомендуется использовать только как fallback в chain mode.
    """

    def __init__(self, api_key: str, timeout: int = 5):
        """
        Args:
            api_key: Google Geocoding API key
            timeout: таймаут запроса в секундах
        """
        self.api_key = api_key
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy initialization Google Maps client"""
        if self._client is None:
            try:
                import googlemaps

                self._client = googlemaps.Client(key=self.api_key, timeout=self.timeout)
            except ImportError:
                logger.warning("googlemaps not installed, Google provider disabled")
                return None
        return self._client

    def geocode(self, place: str, language: str = "en") -> Optional[GeoResult]:
        """Геокодирование через Google Geocoding API"""
        client = self._get_client()
        if not client or not self.api_key:
            return None

        try:
            results = client.geocode(address=place, language=language)

            if not results:
                logger.debug(f"[Google] Place not found: {place}")
                return None

            # Берём первый результат (best match)
            location = results[0]
            geo = location["geometry"]["location"]

            logger.info(f"[Google] Geocoded: {place} → {location['formatted_address']}")

            return GeoResult(
                lat=geo["lat"],
                lon=geo["lng"],
                display_name=location["formatted_address"],
                provider="google",
            )

        except Exception as e:
            logger.warning(f"[Google] Error geocoding {place}: {e}")
            return None


# ============================================================================
# Chain Provider (Nominatim → Google → Hardcoded)
# ============================================================================


class ChainProvider(GeocoderProvider):
    """
    Цепочка провайдеров с fallback.

    Логика:
    1. Пробуем первый провайдер (обычно Nominatim)
    2. Если не удалось → второй (Google)
    3. Если не удалось → hardcoded fallback

    Это оптимальная стратегия:
    - 95% запросов → Nominatim (бесплатно)
    - 4% редких → Google (копейки)
    - 1% offline/CI → hardcoded
    """

    def __init__(self, providers: list[GeocoderProvider]):
        """
        Args:
            providers: список провайдеров в порядке приоритета
        """
        self.providers = providers

    def geocode(self, place: str, language: str = "en") -> Optional[GeoResult]:
        """Пробуем провайдеры по очереди"""
        for provider in self.providers:
            result = provider.geocode(place, language)
            if result:
                return result

        # Последний fallback: hardcoded
        return _geocode_hardcoded(place)


# ============================================================================
# Geocoder Service (с агрессивным кешированием)
# ============================================================================


class GeocoderService:
    """
    Основной сервис геокодирования с агрессивным кешированием.

    Архитектура:
    1. Проверяем cache (БД) по нормализованному ключу
    2. Если нет → вызываем provider
    3. Сохраняем в cache с TTL ~10 лет

    Особенности:
    - Нормализация ключей: "Киев" = "Kiev" = "киев"
    - Один город резолвится только 1 раз для всех пользователей
    - TTL 10 лет (города не меняются часто)
    """

    def __init__(
        self, db: Session, provider: GeocoderProvider, cache_ttl_days: int = 3650
    ):
        """
        Args:
            db: SQLAlchemy сессия
            provider: провайдер геокодирования
            cache_ttl_days: TTL кеша в днях (по умолчанию 10 лет)
        """
        self.db = db
        self.provider = provider
        self.cache_ttl_days = cache_ttl_days

    def _check_cache(self, place_norm: str) -> Optional[GeoResult]:
        """Проверка cache по нормализованному ключу"""
        cached = (
            self.db.query(GeocodeCache)
            .filter(GeocodeCache.place_norm == place_norm)
            .first()
        )

        if not cached:
            return None

        # Проверяем TTL (опционально, можно убрать для вечного cache)
        if self.cache_ttl_days > 0:
            ttl = timedelta(days=self.cache_ttl_days)
            if datetime.utcnow() - cached.created_at > ttl:
                logger.debug(f"[Cache] Expired: {place_norm}")
                return None

        logger.debug(f"[Cache] Hit: {place_norm} → {cached.display_name}")

        return GeoResult(
            lat=cached.lat,
            lon=cached.lon,
            display_name=cached.display_name or place_norm,
            provider="cache",
        )

    def _save_cache(self, place_norm: str, query_raw: str, result: GeoResult):
        """Сохранение результата в cache"""
        try:
            cache_entry = GeocodeCache(
                place_norm=place_norm,
                query_raw=query_raw,
                lat=result.lat,
                lon=result.lon,
                display_name=result.display_name,
                provider=result.provider,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(cache_entry)
            self.db.commit()

            logger.debug(f"[Cache] Saved: {place_norm} → {result.display_name}")

        except Exception as e:
            logger.warning(f"[Cache] Failed to save {place_norm}: {e}")
            self.db.rollback()

    def geocode(self, place: str, language: str = "en") -> Optional[GeoResult]:
        """
        Основной метод геокодирования с кешированием.

        Args:
            place: строка места ("Киев, Украина", "New York, USA")
            language: код языка (en/ru/es/uk)

        Returns:
            GeoResult или None
        """
        if not place:
            return None

        place_norm = _normalize_place(place)

        # 1. Проверяем cache
        cached = self._check_cache(place_norm)
        if cached:
            # #region agent log
            try:
                import json

                with open("debug-e96797.log", "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "sessionId": "e96797",
                                "hypothesisId": "B",
                                "location": "GeocoderService.geocode",
                                "message": "return cached",
                                "data": {
                                    "place_norm": place_norm,
                                    "cache_hit": True,
                                    "lat": cached.lat,
                                    "lon": cached.lon,
                                    "provider": cached.provider,
                                    "lat_repr": repr(cached.lat),
                                    "lon_repr": repr(cached.lon),
                                },
                                "timestamp": __import__("time").time() * 1000,
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion
            return cached

        # 2. Вызываем provider
        result = self.provider.geocode(place, language)
        if not result:
            logger.warning(f"[Geocoder] Failed to geocode: {place}")
            return None

        # 3. Сохраняем в cache
        self._save_cache(place_norm, place, result)
        # #region agent log
        try:
            import json

            with open("debug-e96797.log", "a", encoding="utf-8") as _f:
                _f.write(
                    json.dumps(
                        {
                            "sessionId": "e96797",
                            "hypothesisId": "B",
                            "location": "GeocoderService.geocode",
                            "message": "return from provider",
                            "data": {
                                "place_norm": place_norm,
                                "cache_hit": False,
                                "lat": result.lat,
                                "lon": result.lon,
                                "provider": result.provider,
                                "lat_repr": repr(result.lat),
                                "lon_repr": repr(result.lon),
                            },
                            "timestamp": __import__("time").time() * 1000,
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion
        return result


# ============================================================================
# Factory (для удобного создания сервиса)
# ============================================================================


def get_geocoder_service(
    db: Session,
    mode: str = "chain",
    nominatim_url: str = "https://nominatim.openstreetmap.org",
    nominatim_timeout: int = 5,
    google_api_key: Optional[str] = None,
    google_timeout: int = 5,
    cache_ttl_days: int = 3650,
) -> GeocoderService:
    """
    Фабрика для создания GeocoderService с нужным провайдером.

    Args:
        db: SQLAlchemy сессия
        mode: режим работы
            - "stub": только hardcoded fallback (для тестов)
            - "nominatim": только Nominatim
            - "google": только Google
            - "chain": Nominatim → Google → hardcoded (рекомендуется)
        nominatim_url: URL Nominatim instance
        nominatim_timeout: таймаут Nominatim
        google_api_key: Google API key (опционально)
        google_timeout: таймаут Google
        cache_ttl_days: TTL кеша в днях

    Returns:
        GeocoderService

    Examples:
        # Nominatim only
        geocoder = get_geocoder_service(db, mode="nominatim")

        # Chain (optimal)
        geocoder = get_geocoder_service(
            db,
            mode="chain",
            google_api_key="your_key"
        )

        # Stub (tests)
        geocoder = get_geocoder_service(db, mode="stub")
    """

    if mode == "stub":
        # Только hardcoded (для тестов/CI)
        provider = ChainProvider([])  # пустой chain → сразу hardcoded

    elif mode == "nominatim":
        provider = NominatimProvider(nominatim_url, nominatim_timeout)

    elif mode == "google":
        if not google_api_key:
            logger.warning(
                "Google mode selected but no API key provided, falling back to hardcoded"
            )
            provider = ChainProvider([])
        else:
            provider = GoogleProvider(google_api_key, google_timeout)

    elif mode == "chain":
        providers = []

        # 1. Nominatim (primary, бесплатно)
        providers.append(NominatimProvider(nominatim_url, nominatim_timeout))

        # 2. Google (fallback, платно)
        if google_api_key:
            providers.append(GoogleProvider(google_api_key, google_timeout))

        provider = ChainProvider(providers)

    else:
        raise ValueError(f"Unknown geocoder mode: {mode}")

    return GeocoderService(db, provider, cache_ttl_days)
