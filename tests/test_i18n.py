"""Tests für i18n: Katalog-Coverage, Spracherkennung, Fallback."""
from cloudlockfixer import i18n
from cloudlockfixer.i18n import (
    Language, _CATALOG, available_keys, detect_language, get_language,
    set_language, t,
)
from cloudlockfixer.settings import resolve_language


def setup_function():
    set_language("de")


def test_all_keys_have_both_languages():
    for key, translations in _CATALOG.items():
        assert "de" in translations, f"Key '{key}' missing 'de'"
        assert "en" in translations, f"Key '{key}' missing 'en'"
        assert translations["de"].strip(), f"Key '{key}' has empty 'de'"
        assert translations["en"].strip(), f"Key '{key}' has empty 'en'"


def test_default_language_is_german():
    set_language("de")
    assert get_language() == "de"


def test_german_translation():
    set_language("de")
    assert t("quit_label") == "Beenden"
    assert t("run_now") == "Jetzt ausführen"
    assert t("queue_empty") == "Queue leer."


def test_english_translation():
    set_language("en")
    assert t("quit_label") == "Quit"
    assert t("run_now") == "Run now"
    assert t("queue_empty") == "Queue empty."


def test_unknown_key_returns_key():
    assert t("nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_format_parameters():
    set_language("de")
    result = t("status_open", n=5, failed=2)
    assert "5" in result and "2" in result

    set_language("en")
    result = t("status_open", n=3, failed=1)
    assert "3" in result and "1" in result


def test_format_missing_param_returns_template():
    set_language("de")
    result = t("status_open")
    assert "{n}" in result or "offen" in result


def test_detect_language_german(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: ("de_DE", "UTF-8"))
    assert detect_language() == "de"


def test_detect_language_english(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: ("en_US", "UTF-8"))
    assert detect_language() == "en"


def test_detect_language_fallback(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: (None, None))
    assert detect_language() == "de"


def test_available_keys_sorted():
    keys = available_keys()
    assert keys == sorted(keys)
    assert len(keys) > 40


def test_resolve_language_auto(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: ("en_US", "UTF-8"))
    assert resolve_language({"language": "auto"}) == "en"


def test_resolve_language_explicit():
    assert resolve_language({"language": "de"}) == "de"
    assert resolve_language({"language": "en"}) == "en"


def test_resolve_language_default():
    assert resolve_language({}) in ("de", "en")
