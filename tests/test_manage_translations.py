"""Hermetische Vertragstests für das Translation-Management-Tooling (manage_translations.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import manage_translations as mt
from cloudlockfixer import manage_translations as pkg_mt
from cloudlockfixer.i18n import export_catalog_json

ROOT = Path(__file__).resolve().parents[1]
REAL_CATALOG = ROOT / "locales" / "translations.json"


def test_validate_catalog_success_on_real_catalog():
    """Der produktive Katalog muss 100% Parität über alle 6 Zielsprachen aufweisen."""
    assert REAL_CATALOG.exists(), f"Katalogdatei fehlt: {REAL_CATALOG}"
    is_valid, findings = mt.validate_catalog(REAL_CATALOG)
    assert is_valid is True, f"Paritätsbefunde gefunden: {findings}"
    assert len(findings) == 0


def test_validate_catalog_detects_missing_language_slot(tmp_path: Path):
    """Fehlende Sprachschlüssel müssen zuverlässig erkannt werden."""
    dummy = tmp_path / "translations.json"
    data = {
        "_meta": {"description": "test"},
        "btn_test": {"de": "Test", "en": "Test", "es": "Prueba", "zh": "测试", "ja": "テスト"},
    }
    dummy.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    is_valid, findings = mt.validate_catalog(dummy)
    assert is_valid is False
    assert any("ru" in f and "btn_test" in f for f in findings)


def test_validate_catalog_detects_empty_translation(tmp_path: Path):
    """Leere Übersetzungs-Strings müssen als Befund gemeldet werden."""
    dummy = tmp_path / "translations.json"
    data = {
        "btn_empty": {"de": "Leer", "en": "", "es": "Vacío", "zh": "空", "ja": "空", "ru": "Пусто"},
    }
    dummy.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    is_valid, findings = mt.validate_catalog(dummy)
    assert is_valid is False
    assert any("btn_empty" in f and "en" in f for f in findings)


def test_validate_catalog_detects_missing_file(tmp_path: Path):
    """Nicht existierende Katalogdateien müssen mit is_valid=False quittiert werden."""
    missing = tmp_path / "non_existent.json"
    is_valid, findings = mt.validate_catalog(missing)
    assert is_valid is False
    assert any("existiert nicht" in f for f in findings)


def test_validate_catalog_detects_corrupt_json(tmp_path: Path):
    """Korruptes JSON muss abgefangen und als Befund gemeldet werden."""
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{this is not valid json", encoding="utf-8")

    is_valid, findings = mt.validate_catalog(corrupt)
    assert is_valid is False
    assert any("JSON-Parsing-Fehler" in f for f in findings)


def test_validate_catalog_detects_invalid_root_type(tmp_path: Path):
    """Eine JSON-Wurzel, die kein Dict ist, muss abgelehnt werden."""
    invalid_root = tmp_path / "array.json"
    invalid_root.write_text("[\"item1\", \"item2\"]", encoding="utf-8")

    is_valid, findings = mt.validate_catalog(invalid_root)
    assert is_valid is False
    assert any("Wurzel ist kein Dictionary" in f for f in findings)


def test_validate_catalog_detects_invalid_entry_type(tmp_path: Path):
    """Ein Schlüsselwert, der kein Dict ist, muss gemeldet werden."""
    invalid_entry = tmp_path / "invalid_entry.json"
    invalid_entry.write_text(json.dumps({"key_primitive": "plain_string"}), encoding="utf-8")

    is_valid, findings = mt.validate_catalog(invalid_entry)
    assert is_valid is False
    assert any("kein Objekt mit Sprachschlüsseln" in f for f in findings)


def test_get_catalog_stats_structure():
    """get_catalog_stats muss eine vollständige Metadaten- und Sprachstruktur liefern."""
    stats = mt.get_catalog_stats(REAL_CATALOG)
    assert stats["total_keys"] >= 120
    assert stats["perfect_parity"] is True
    assert set(stats["languages"].keys()) == {"de", "en", "es", "zh", "ja", "ru"}
    for lang in ("de", "en", "es", "zh", "ja", "ru"):
        assert stats["languages"][lang]["filled"] == stats["total_keys"]
        assert stats["languages"][lang]["missing"] == 0
        assert stats["languages"][lang]["coverage_percent"] == 100.0


def test_atomic_save_translations_durability(tmp_path: Path):
    """save_translations muss die Datei atomar schreiben und sauberes JSON erzeugen."""
    target = tmp_path / "out" / "translations.json"
    payload = {"_meta": {"test": 1}, "key1": {"de": "Hallo", "en": "Hello"}}

    mt.save_translations(target, payload)
    assert target.exists()

    loaded = mt.load_translations(target)
    assert loaded == payload

    # Prüfen, dass keine verwaisten .tmp-Dateien zurückbleiben
    tmp_files = list(target.parent.glob(".*.tmp.*"))
    assert len(tmp_files) == 0


def test_atomic_save_translations_preserves_on_failure(tmp_path: Path):
    """Bei einem Serialisierungsfehler darf eine bestehende Datei nicht zerstört werden."""
    target = tmp_path / "translations.json"
    initial_payload = {"key_keep": {"de": "Erhalten"}}
    mt.save_translations(target, initial_payload)

    # Nicht serialisierbares Objekt übergeben
    with pytest.raises(TypeError):
        mt.save_translations(target, {"corrupt": object()})

    # Vorheriger Inhalt muss unversehrt existieren
    assert mt.load_translations(target) == initial_payload


def test_cli_check_flag_exit_0():
    """main(['--check']) muss Exit-Code 0 auf dem echten Katalog liefern."""
    exit_code = mt.main(["--check", "--dir", str(ROOT)])
    assert exit_code == 0


def test_cli_check_flag_exit_1_on_invalid(tmp_path: Path):
    """main(['--check']) muss Exit-Code 1 liefern, wenn der Katalog Lücken aufweist."""
    broken = tmp_path / "translations.json"
    broken.write_text(json.dumps({"key_x": {"de": "X", "en": ""}}), encoding="utf-8")

    exit_code = mt.main(["--check", "--dir", str(broken)])
    assert exit_code == 1


def test_cli_stats_flag_output(capsys: pytest.CaptureFixture[str]):
    """main(['--stats']) muss formatierten Output auf stdout schreiben."""
    exit_code = mt.main(["--stats", "--dir", str(ROOT)])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "CloudLockFixer - Tier-2 Übersetzungskatalog-Statistiken" in captured.out
    assert "Inhaltsschlüssel:" in captured.out
    assert "100% perfekte Parität" in captured.out


def test_cli_stats_flag_json_output(capsys: pytest.CaptureFixture[str]):
    """main(['--stats', '--json']) muss valides JSON auf stdout schreiben."""
    exit_code = mt.main(["--stats", "--json", "--dir", str(ROOT)])
    assert exit_code == 0

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["perfect_parity"] is True
    assert parsed["total_keys"] >= 120
    assert "de" in parsed["languages"]


def test_root_and_package_manage_translations_parity():
    """Root- und Package-Modul müssen dieselbe API bereitstellen und paritätisch sein."""
    assert mt.SUPPORTED_LANGUAGES == pkg_mt.SUPPORTED_LANGUAGES
    assert mt.DEFAULT_LANGUAGE == pkg_mt.DEFAULT_LANGUAGE

    root_stats = mt.get_catalog_stats(REAL_CATALOG)
    pkg_stats = pkg_mt.get_catalog_stats(REAL_CATALOG)
    assert root_stats["total_keys"] == pkg_stats["total_keys"]
    assert root_stats["perfect_parity"] == pkg_stats["perfect_parity"]


def test_export_catalog_json_atomic_durability(tmp_path: Path):
    """export_catalog_json muss die Übersetzungen atomar exportieren."""
    export_target = tmp_path / "exported_translations.json"
    res = export_catalog_json(export_target)
    assert res == export_target
    assert export_target.exists()

    with open(export_target, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert len(data) >= 120

    # Keine verwaisten tmp-Dateien
    assert len(list(tmp_path.glob(".*.tmp.*"))) == 0
