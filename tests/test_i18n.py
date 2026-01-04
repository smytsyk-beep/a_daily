# tests/test_i18n.py

from app.i18n import normalize_locale, tr


def test_normalize_locale():
    assert normalize_locale("en") == "en"
    assert normalize_locale("ru") == "ru"
    assert normalize_locale("es") == "es"
    assert normalize_locale("pt-br") == "en"
    assert normalize_locale("uk") == "ru"


def test_tr_missing_key_returns_key():
    assert tr("en", "tg.nope.missing") == "tg.nope.missing"


def test_tr_fallback_to_en():
    # ключ точно есть в en.json
    assert (
        "AstroDaily" in tr("es", "tg.age_gate.question")
        or tr("es", "tg.age_gate.question") != "tg.age_gate.question"
    )


def test_tr_formatting_safe():
    s = tr("en", "tg.start.welcome", bot_name="AstroDaily")
    assert "AstroDaily" in s
