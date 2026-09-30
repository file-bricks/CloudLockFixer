"""Tests für i18n: Katalog-Coverage (Tier-2: 6 Sprachen), Spracherkennung, Fallback."""
from cloudlockfixer.i18n import (
    _CATALOG, available_keys, detect_language, get_language,
    set_language, t,
    SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, FALLBACK_CHAIN, LANGUAGE_DISPLAY_NAMES,
)
from cloudlockfixer.settings import resolve_language

LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")


def setup_function():
    set_language("de")


def test_all_keys_have_all_six_languages():
    for key, translations in _CATALOG.items():
        for lang in LANGUAGES:
            assert lang in translations, f"Key '{key}' missing '{lang}'"
            assert translations[lang].strip(), f"Key '{key}' has empty '{lang}'"


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
    assert t("open_data_folder") == "Open data folder"


def test_spanish_translation():
    set_language("es")
    assert t("quit_label") == "Salir"
    assert t("run_now") == "Ejecutar ahora"
    assert t("queue_empty") == "Cola vacía."
    assert t("open_data_folder") == "Abrir carpeta de datos"


def test_chinese_translation():
    set_language("zh")
    assert t("quit_label") == "退出"
    assert t("run_now") == "立即运行"
    assert t("queue_empty") == "队列为空。"
    assert t("open_data_folder") == "打开数据文件夹"


def test_japanese_translation():
    set_language("ja")
    assert t("quit_label") == "終了"
    assert t("run_now") == "今すぐ実行"
    assert t("queue_empty") == "キューは空です。"
    assert t("open_data_folder") == "データフォルダーを開く"


def test_russian_translation():
    set_language("ru")
    assert t("quit_label") == "Выход"
    assert t("run_now") == "Запустить сейчас"
    assert t("queue_empty") == "Очередь пуста."
    assert t("open_data_folder") == "Открыть папку с данными"


def test_open_data_folder_label_matches_action_scope():
    set_language("de")
    assert t("open_data_folder") == "Datenordner öffnen"

    set_language("en")
    assert "folder" in t("open_data_folder").lower()

    set_language("es")
    assert "carpeta" in t("open_data_folder").lower()


def test_unknown_key_returns_key():
    assert t("nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_format_parameters():
    set_language("de")
    result = t("status_open", n=5, retrying=2, failed=1)
    assert "5" in result and "2" in result and "1" in result

    set_language("en")
    result = t("status_open", n=3, retrying=1, failed=4)
    assert "3" in result and "1" in result and "4" in result

    set_language("es")
    result = t("status_open", n=7, retrying=2, failed=3)
    assert "7" in result and "2" in result and "3" in result

    set_language("zh")
    result = t("status_open", n=8, retrying=3, failed=2)
    assert "8" in result and "3" in result and "2" in result

    set_language("ja")
    result = t("status_open", n=4, retrying=1, failed=2)
    assert "4" in result and "1" in result and "2" in result

    set_language("ru")
    result = t("status_open", n=9, retrying=4, failed=1)
    assert "9" in result and "4" in result and "1" in result


def test_run_summary_formats_permanent_failures():
    set_language("en")
    result = t("run_summary", done=0, failed=1, permanent=2, start=3, paused="")
    assert "2 permanently failed" in result

    set_language("es")
    result = t("run_summary", done=1, failed=0, permanent=3, start=4, paused="")
    assert "3 fallida(s) permanente(s)" in result

    set_language("zh")
    result = t("run_summary", done=2, failed=0, permanent=1, start=3, paused="")
    assert "1 个永久失败" in result


def test_format_missing_param_returns_template():
    set_language("de")
    result = t("status_open")
    assert "{n}" in result or "offen" in result


def test_detect_language_locales(monkeypatch):
    locales = [
        (("de_DE", "UTF-8"), "de"),
        (("en_US", "UTF-8"), "en"),
        (("es_ES", "UTF-8"), "es"),
        (("zh_CN", "UTF-8"), "zh"),
        (("ja_JP", "UTF-8"), "ja"),
        (("ru_RU", "UTF-8"), "ru"),
    ]
    for loc, expected in locales:
        monkeypatch.setattr("locale.getlocale", lambda target_loc=loc: target_loc)
        assert detect_language() == expected


def test_detect_language_fallback(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: (None, None))
    assert detect_language() == "de"


def test_detect_language_locale_error_falls_back_to_german(monkeypatch):
    """Bug-Fix: locale.getlocale() kann locale.Error werfen (Subclass von Exception,
    nicht von ValueError/TypeError). Muss sicher auf 'de' zurückfallen."""
    import locale as locale_mod

    def raise_locale_error():
        raise locale_mod.Error("Ungültige Locale-Konfiguration")

    monkeypatch.setattr("locale.getlocale", raise_locale_error)
    result = detect_language()
    assert result == "de", f"Erwartet 'de' als Fallback bei locale.Error, war: {result}"


def test_available_keys_sorted():
    keys = available_keys()
    assert keys == sorted(keys)
    assert len(keys) >= 50


def test_resolve_language_auto(monkeypatch):
    monkeypatch.setattr("locale.getlocale", lambda: ("en_US", "UTF-8"))
    assert resolve_language({"language": "auto"}) == "en"

    monkeypatch.setattr("locale.getlocale", lambda: ("es_ES", "UTF-8"))
    assert resolve_language({"language": "auto"}) == "es"


def test_resolve_language_explicit():
    for lang in LANGUAGES:
        assert resolve_language({"language": lang}) == lang


def test_resolve_language_default():
    assert resolve_language({}) in LANGUAGES


def test_i18n_constants_and_displays():
    assert SUPPORTED_LANGUAGES == ("de", "en", "es", "zh", "ja", "ru")
    assert DEFAULT_LANGUAGE == "de"
    assert FALLBACK_CHAIN == ("en", "de")
    for lang in SUPPORTED_LANGUAGES:
        assert lang in LANGUAGE_DISPLAY_NAMES
        assert len(LANGUAGE_DISPLAY_NAMES[lang]) > 0


def test_four_stage_fallback_chain(monkeypatch):
    """Testet die 4-stufige Kette: target -> en -> de -> key."""
    fake_catalog = {
        "full_key": {"de": "DE-Text", "en": "EN-Text", "es": "ES-Text"},
        "missing_es": {"de": "DE-Fallback", "en": "EN-Fallback"},
        "missing_es_and_en": {"de": "DE-Nur"},
    }
    monkeypatch.setattr("cloudlockfixer.i18n._CATALOG", fake_catalog)

    set_language("es")
    # 1. Target vorhanden
    assert t("full_key") == "ES-Text"
    # 2. Target fehlt -> Fallback auf en
    assert t("missing_es") == "EN-Fallback"
    # 3. Target und en fehlen -> Fallback auf de
    assert t("missing_es_and_en") == "DE-Nur"
    # 4. Key existiert gar nicht -> Key selbst
    assert t("completely_unknown_key") == "completely_unknown_key"

    # Reset
    set_language("de")


def test_translations_json_parity():
    """Stellt sicher, dass locales/translations.json existiert und mit _CATALOG übereinstimmt."""
    import json
    from pathlib import Path

    json_path = Path(__file__).resolve().parents[1] / "locales" / "translations.json"
    assert json_path.is_file(), "locales/translations.json muss existieren"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert set(data.keys()) == set(_CATALOG.keys())
    for key, val in _CATALOG.items():
        assert data[key] == val


def test_manage_translations_check_audit():
    """Prüft, ob manage_translations.py im Check-Modus 0 zurückgibt."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import manage_translations

    assert manage_translations.audit_catalog(check_mode=True) == 0


def test_readme_spanish_tier2_parity():
    """Prüft strukturelle Parität von README.es.md gemäß Policy P-006."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    readme_es = root / "README.es.md"
    assert readme_es.is_file(), "README.es.md muss existieren"

    text = readme_es.read_text(encoding="utf-8")
    assert len(text) >= 4000
    assert "assets/banner.svg" in text
    assert "README.md" in text
    assert "README.de.md" in text
    assert "docs/DESIGN.md" in text
    assert "LICENSE" in text
    assert "```mermaid" in text
    assert "flowchart TD" in text
    assert "sequenceDiagram" in text
    assert "file-bricks/SoftwareCenter" in text
