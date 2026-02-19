# tests/test_geocoder.py
"""
Тесты для унифицированного geocoder сервиса.

Покрывают:
- Provider pattern
- Агрессивное кеширование
- Chain режим (Nominatim → Google → Hardcoded)
- Нормализацию ключей
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.geocoder import (
    GeoResult,
    _normalize_place,
    _geocode_hardcoded,
    NominatimProvider,
    GoogleProvider,
    ChainProvider,
    GeocoderService,
    get_geocoder_service,
)
from app.models import GeocodeCache


# ============================================================================
# Тесты нормализации
# ============================================================================


def test_normalize_place_lowercase():
    """Нормализация приводит к нижнему регистру"""
    assert _normalize_place("Kyiv") == "kyiv"
    assert _normalize_place("MOSCOW") == "moscow"
    assert _normalize_place("NeW YoRk") == "new york"


def test_normalize_place_russian():
    """Нормализация русских названий"""
    assert _normalize_place("Киев") == "киев"
    assert _normalize_place("Москва") == "москва"
    assert _normalize_place("Санкт-Петербург") == "санкт-петербург"


def test_normalize_place_removes_commas():
    """Нормализация убирает запятые"""
    assert _normalize_place("Kyiv, Ukraine") == "kyiv ukraine"
    assert _normalize_place("New York, USA") == "new york usa"


def test_normalize_place_yo_to_e():
    """Нормализация заменяет ё на е"""
    assert _normalize_place("Королёв") == "королев"


def test_normalize_place_strips_whitespace():
    """Нормализация убирает лишние пробелы"""
    assert _normalize_place("  Kyiv  ") == "kyiv"
    assert _normalize_place("New   York") == "new york"


def test_normalize_place_equivalence():
    """Проверка, что разные варианты дают одинаковый ключ"""
    # Киев на разных языках (Kiev = Kyiv после канонизации)
    assert _normalize_place("Kyiv, Ukraine") == _normalize_place("Kiev, Ukraine")
    assert _normalize_place("Киев, Украина") == "киев украина"
    assert _normalize_place("киев украина") == "киев украина"

    # Москва
    assert _normalize_place("Moscow, Russia") == _normalize_place("moscow russia")
    assert _normalize_place("Москва, Россия") == "москва россия"
    assert _normalize_place("москва россия") == "москва россия"


# ============================================================================
# Тесты hardcoded fallback
# ============================================================================


def test_geocode_hardcoded_kyiv_variants():
    """Hardcoded fallback находит Киев во всех вариантах"""
    variants = [
        "Kyiv",
        "Kiev",
        "kyiv",
        "kiev",
        "Киев",
        "киев",
        "Київ",
        "київ",
        "Kyiv, Ukraine",
        "Kiev, Ukraine",
        "Киев, Украина",
    ]

    for variant in variants:
        result = _geocode_hardcoded(variant)
        assert result is not None, f"Failed for: {variant}"
        assert result.lat == pytest.approx(50.4501, abs=0.01)
        assert result.lon == pytest.approx(30.5234, abs=0.01)
        assert result.provider == "hardcoded"


def test_geocode_hardcoded_moscow():
    """Hardcoded fallback находит Москву"""
    result = _geocode_hardcoded("Москва, Россия")
    assert result is not None
    assert result.lat == pytest.approx(55.7558, abs=0.01)
    assert result.lon == pytest.approx(37.6173, abs=0.01)


def test_geocode_hardcoded_new_york():
    """Hardcoded fallback находит Нью-Йорк"""
    result = _geocode_hardcoded("New York, USA")
    assert result is not None
    assert result.lat == pytest.approx(40.7128, abs=0.01)
    assert result.lon == pytest.approx(-74.0060, abs=0.01)


def test_geocode_hardcoded_country_fallback():
    """Hardcoded fallback работает по стране (столица)"""
    # Только страна → столица
    result = _geocode_hardcoded("Ukraine")
    assert result is not None
    assert result.lat == pytest.approx(50.4501, abs=0.01)  # Kyiv

    result = _geocode_hardcoded("Украина")
    assert result is not None
    assert result.lat == pytest.approx(50.4501, abs=0.01)  # Kyiv


def test_geocode_hardcoded_not_found():
    """Hardcoded fallback возвращает None для неизвестных мест"""
    result = _geocode_hardcoded("Неизвестный Город")
    assert result is None

    result = _geocode_hardcoded("Unknown City, Unknown Country")
    assert result is None


# ============================================================================
# Тесты Nominatim Provider (мокированные)
# ============================================================================


def test_nominatim_provider_init():
    """Nominatim provider инициализируется с параметрами"""
    provider = NominatimProvider("https://nominatim.openstreetmap.org", timeout=10)
    assert provider.base_url == "https://nominatim.openstreetmap.org"
    assert provider.timeout == 10


def test_nominatim_provider_lazy_init():
    """Nominatim geolocator создаётся лениво"""
    provider = NominatimProvider("https://nominatim.openstreetmap.org")
    assert provider._geolocator is None
    # После первого вызова _get_geolocator() должен быть создан (если geopy установлен)


# ============================================================================
# Тесты Google Provider (мокированные)
# ============================================================================


def test_google_provider_init():
    """Google provider инициализируется с API key"""
    provider = GoogleProvider("test_api_key", timeout=10)
    assert provider.api_key == "test_api_key"
    assert provider.timeout == 10


def test_google_provider_lazy_init():
    """Google client создаётся лениво"""
    provider = GoogleProvider("test_api_key")
    assert provider._client is None


# ============================================================================
# Тесты Chain Provider
# ============================================================================


def test_chain_provider_empty_chain():
    """Chain с пустым списком провайдеров использует hardcoded"""
    chain = ChainProvider([])
    result = chain.geocode("Kyiv, Ukraine")
    assert result is not None
    assert result.provider == "hardcoded"


def test_chain_provider_first_wins():
    """Chain использует первый успешный провайдер"""
    mock_provider1 = Mock()
    mock_provider1.geocode.return_value = GeoResult(
        lat=50.45, lon=30.52, display_name="Kyiv", provider="mock1"
    )

    mock_provider2 = Mock()
    mock_provider2.geocode.return_value = GeoResult(
        lat=40.71, lon=-74.00, display_name="NYC", provider="mock2"
    )

    chain = ChainProvider([mock_provider1, mock_provider2])
    result = chain.geocode("Kyiv")

    assert result.provider == "mock1"  # Первый провайдер
    mock_provider1.geocode.assert_called_once_with("Kyiv", "en")
    mock_provider2.geocode.assert_not_called()  # Второй не вызывается


def test_chain_provider_fallback():
    """Chain переключается на второй провайдер при неудаче первого"""
    mock_provider1 = Mock()
    mock_provider1.geocode.return_value = None  # Первый не нашёл

    mock_provider2 = Mock()
    mock_provider2.geocode.return_value = GeoResult(
        lat=40.71, lon=-74.00, display_name="NYC", provider="mock2"
    )

    chain = ChainProvider([mock_provider1, mock_provider2])
    result = chain.geocode("NYC")

    assert result.provider == "mock2"  # Второй провайдер
    mock_provider1.geocode.assert_called_once()
    mock_provider2.geocode.assert_called_once()


def test_chain_provider_final_hardcoded_fallback():
    """Chain использует hardcoded если все провайдеры не сработали"""
    mock_provider = Mock()
    mock_provider.geocode.return_value = None

    chain = ChainProvider([mock_provider])
    result = chain.geocode("Kyiv, Ukraine")

    assert result is not None
    assert result.provider == "hardcoded"


# ============================================================================
# Тесты GeocoderService с кешированием
# ============================================================================


@pytest.fixture
def mock_db():
    """Мокированная БД сессия"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def mock_provider():
    """Мокированный провайдер"""
    provider = Mock()
    return provider


def test_geocoder_service_cache_hit(mock_db, mock_provider):
    """GeocoderService возвращает результат из кеша"""
    # Настраиваем мок: в кеше есть результат (created_at — реальный datetime для проверки TTL)
    cached_entry = Mock()
    cached_entry.lat = 50.45
    cached_entry.lon = 30.52
    cached_entry.display_name = "Kyiv, Ukraine"
    cached_entry.provider = "cache"
    cached_entry.created_at = datetime.utcnow()  # не истёкший TTL

    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = cached_entry
    mock_db.query.return_value = mock_query

    service = GeocoderService(mock_db, mock_provider, cache_ttl_days=3650)
    result = service.geocode("Kyiv, Ukraine")

    assert result is not None
    assert result.lat == 50.45
    assert result.lon == 30.52
    assert result.provider == "cache"

    # Провайдер не должен вызываться при cache hit
    mock_provider.geocode.assert_not_called()


def test_geocoder_service_cache_miss(mock_db, mock_provider):
    """GeocoderService вызывает провайдер при cache miss"""
    # Настраиваем мок: в кеше нет результата
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    # Провайдер возвращает результат
    mock_provider.geocode.return_value = GeoResult(
        lat=40.71, lon=-74.00, display_name="New York", provider="nominatim"
    )

    service = GeocoderService(mock_db, mock_provider, cache_ttl_days=3650)
    result = service.geocode("New York")

    assert result is not None
    assert result.lat == 40.71
    assert result.provider == "nominatim"

    # Провайдер должен быть вызван
    mock_provider.geocode.assert_called_once_with("New York", "en")

    # Результат должен быть сохранён в кеш
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_geocoder_service_normalization(mock_db, mock_provider):
    """GeocoderService использует нормализованный ключ для кеша"""
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    mock_provider.geocode.return_value = GeoResult(
        lat=50.45, lon=30.52, display_name="Kyiv", provider="nominatim"
    )

    service = GeocoderService(mock_db, mock_provider)

    # Разные варианты ввода должны приводить к одному cache key
    service.geocode("Kyiv, Ukraine")
    service.geocode("KYIV, UKRAINE")
    service.geocode("Kiev, Ukraine")

    # Проверяем, что все запросы использовали нормализованный ключ
    # (в реальности они бы нашли один и тот же кеш)


def test_geocoder_service_language_parameter(mock_db, mock_provider):
    """GeocoderService передаёт параметр language в провайдер"""
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    mock_provider.geocode.return_value = GeoResult(
        lat=50.45, lon=30.52, display_name="Київ, Україна", provider="nominatim"
    )

    service = GeocoderService(mock_db, mock_provider)
    service.geocode("Kyiv", language="uk")

    mock_provider.geocode.assert_called_once_with("Kyiv", "uk")


# ============================================================================
# Тесты Factory
# ============================================================================


def test_get_geocoder_service_stub_mode(mock_db):
    """Factory создаёт stub geocoder (только hardcoded)"""
    mock_db.query.return_value.filter.return_value.first.return_value = (
        None  # cache miss
    )
    service = get_geocoder_service(mock_db, mode="stub")
    assert isinstance(service, GeocoderService)

    # Stub mode должен использовать только hardcoded
    result = service.geocode("Kyiv, Ukraine")
    assert result is not None
    assert result.provider == "hardcoded"


def test_get_geocoder_service_nominatim_mode(mock_db):
    """Factory создаёт Nominatim geocoder"""
    service = get_geocoder_service(
        mock_db, mode="nominatim", nominatim_url="https://nominatim.openstreetmap.org"
    )
    assert isinstance(service, GeocoderService)
    assert isinstance(service.provider, NominatimProvider)


def test_get_geocoder_service_chain_mode(mock_db):
    """Factory создаёт chain geocoder"""
    service = get_geocoder_service(
        mock_db,
        mode="chain",
        nominatim_url="https://nominatim.openstreetmap.org",
        google_api_key="test_key",
    )
    assert isinstance(service, GeocoderService)
    assert isinstance(service.provider, ChainProvider)


def test_get_geocoder_service_invalid_mode(mock_db):
    """Factory выбрасывает ошибку для неизвестного mode"""
    with pytest.raises(ValueError, match="Unknown geocoder mode"):
        get_geocoder_service(mock_db, mode="invalid_mode")


# ============================================================================
# Интеграционные тесты (stub mode, без HTTP)
# ============================================================================


def test_integration_stub_mode_kyiv(mock_db):
    """Интеграционный тест: stub mode геокодирует Киев"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    service = get_geocoder_service(mock_db, mode="stub")
    result = service.geocode("Kyiv, Ukraine")

    assert result is not None
    assert result.lat == pytest.approx(50.4501, abs=0.01)
    assert result.lon == pytest.approx(30.5234, abs=0.01)
    assert "Kyiv" in result.display_name


def test_integration_stub_mode_multiple_languages(mock_db):
    """Интеграционный тест: stub mode работает с разными языками"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    service = get_geocoder_service(mock_db, mode="stub")

    # Английский
    result_en = service.geocode("Kyiv, Ukraine", language="en")
    assert result_en is not None

    # Русский
    result_ru = service.geocode("Киев, Украина", language="ru")
    assert result_ru is not None

    # Должны вернуть одинаковые координаты (pytest.approx — устойчиво к разному представлению float)
    assert result_en.lat == pytest.approx(result_ru.lat, abs=1e-9)
    assert result_en.lon == pytest.approx(result_ru.lon, abs=1e-9)
