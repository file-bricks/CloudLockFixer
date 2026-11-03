#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_translations.py - Multi-Language Translation Manager & CI Gate
======================================================================
Verwaltet, validiert und auditiert den Übersetzungskatalog locales/translations.json
gemäß Richtlinie Policy P-006 Tier-2 (DE, EN, ES, ZH, JA, RU) für CloudLockFixer.

Funktionen:
- Strikte Paritätsprüfung (--check) aller 6 Zielsprachen für CI/Automationen (Exit 0/1)
- Detaillierte Übersichtsstatistiken (--stats) mit Zählungen und Abdeckungsgrad je Sprache
- Quellcode-Scanner (--scan) für deutsche GUI-Strings und t()-Aufrufe in .py-Dateien
- Strukturierte JSON-Ausgabe (--json) für CI/Agenten-Pipelines
- Crash-feste, atomare Persistenz via Staging-Datei (.tmp.<pid>_<uuid>), flush() und fsync()

Verwendung:
    python manage_translations.py --check
    python manage_translations.py --stats [--json]
    python manage_translations.py [--dir PROJEKTVERZEICHNIS] [--scan]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

# Defensives Konsolen-Encoding unter Windows sicherstellen
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            with contextlib.suppress(OSError, ValueError, AttributeError):
                stream.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("CloudLockFixer.ManageTranslations")

SUPPORTED_LANGUAGES = ["de", "en", "es", "zh", "ja", "ru"]
DEFAULT_LANGUAGE = "de"

# Typische GUI- und Dialog-Muster in Python/PySide6
STRING_PATTERNS = [
    re.compile(r'text\s*=\s*"([^"\n]+)"'),
    re.compile(r'setText\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setWindowTitle\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setToolTip\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setStatusTip\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setAccessibleName\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setAccessibleDescription\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'QLabel\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'QPushButton\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'addAction\s*\([^,\n]*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'addTab\s*\([^,\n]+,\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'\bt\(\s*["\']([^"\'\n]+)["\']\s*\)'),
]

GERMAN_HINTS = [
    "datei", "bearbeiten", "ansicht", "hilfe", "öffnen", "speichern",
    "schließen", "einstellungen", "abbrechen", "ok", "ja", "nein",
    "start", "stop", "pause", "fortsetzen", "laden", "aktualisieren",
    "filter", "fehler", "export", "import", "optionen", "anzeigen",
    "warteschlange", "sperre", "wiederholen", "freigeben", "entsperren",
    "löschen", "entfernen", "hinzufügen", "zurücksetzen", "tastaturkürzel",
    "erweitert", "status", "protokoll", "dienst", "provider",
]


def is_german_hint(text: str) -> bool:
    """Heuristik: Erkennt, ob ein Text deutscher Natur ist."""
    lower = text.lower()
    if any(c in lower for c in ("ä", "ö", "ü", "ß")):
        return True
    words = set(re.findall(r"[a-zäöüß]+", lower))
    return any(hint in words for hint in GERMAN_HINTS)


def resolve_translation_file(base_dir: Path | str | None = None) -> Path:
    """Findet den kanonischen Pfad zu translations.json."""
    if base_dir:
        p = Path(base_dir)
        if p.is_file() and p.name.endswith(".json"):
            return p.resolve()
        candidates = [
            p / "locales" / "translations.json",
            p / "src" / "cloudlockfixer" / "locales" / "translations.json",
            p / "translations.json",
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()
        return (p / "locales" / "translations.json").resolve()

    root = Path(__file__).resolve().parent
    candidates = [
        root / "locales" / "translations.json",
        root / "src" / "cloudlockfixer" / "locales" / "translations.json",
        root / "translations.json",
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    return (root / "locales" / "translations.json").resolve()


def load_translations(trans_file: Path | str) -> dict[str, Any]:
    """Lädt den Übersetzungskatalog ein."""
    path = Path(trans_file)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_translations(trans_file: Path | str, translations: dict[str, Any]) -> None:
    """Persistiert den Katalog atomar via Staging-Datei (.tmp.<pid>_<uuid>), flush() und fsync()."""
    target = Path(trans_file).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    nonce = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
    tmp_path = target.parent / f".{target.name}.tmp.{nonce}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if sys.platform == "win32" and target.exists():
            with contextlib.suppress(OSError):
                os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()




def audit_catalog(check_mode: bool = False, base_dir: Path | str | None = None) -> int:
    """Rückwärtskompatible Audit-Fassade für ältere Tests und Skripte."""
    trans_file = resolve_translation_file(base_dir)
    is_valid, findings = validate_catalog(trans_file)
    if not is_valid:
        for f in findings:
            print(f"[FAIL] {f}")
        return 1
    print(f"[OK] 100% Parität über alle {len(SUPPORTED_LANGUAGES)} Sprachen ({', '.join(SUPPORTED_LANGUAGES)}).")
    return 0

def validate_catalog(trans_file: Path | str) -> tuple[bool, list[str]]:
    """
    Validiert die Tier-2 6-Sprachen-Parität (DE, EN, ES, ZH, JA, RU).
    Gibt (is_valid, findings) zurück.
    """
    path = Path(trans_file)
    findings: list[str] = []

    if not path.exists():
        findings.append(f"Übersetzungsdatei existiert nicht: {path}")
        return False, findings

    try:
        data = load_translations(path)
    except Exception as e:
        findings.append(f"JSON-Parsing-Fehler in {path}: {e}")
        return False, findings

    if not isinstance(data, dict):
        findings.append(f"Ungültige JSON-Struktur in {path}: Wurzel ist kein Dictionary")
        return False, findings

    keys_checked = 0
    for key, val in data.items():
        if key.startswith("_"):
            continue  # Metadaten-Eintrag überspringen
        keys_checked += 1

        if not isinstance(val, dict):
            findings.append(f"Schlüssel '{key}': Wert ist kein Objekt mit Sprachschlüsseln")
            continue

        for lang in SUPPORTED_LANGUAGES:
            if lang not in val:
                findings.append(f"Schlüssel '{key}': Fehlender Sprachslot '{lang}'")
            elif val[lang] is None or not str(val[lang]).strip():
                findings.append(f"Schlüssel '{key}': Leere Übersetzung für Sprache '{lang}'")

    if keys_checked == 0:
        findings.append("Katalog enthält keine Inhaltsschlüssel")

    return (len(findings) == 0, findings)


def get_catalog_stats(trans_file: Path | str) -> dict[str, Any]:
    """Erzeugt eine statistische Auswertung der Sprachabdeckung."""
    path = Path(trans_file)
    data = load_translations(path) if path.exists() else {}

    keys = [k for k in data.keys() if not k.startswith("_")]
    total_keys = len(keys)

    lang_stats: dict[str, dict[str, Any]] = {}
    perfect_parity = True

    for lang in SUPPORTED_LANGUAGES:
        filled = 0
        missing = 0
        for k in keys:
            val = data.get(k, {})
            if isinstance(val, dict) and val.get(lang) and str(val[lang]).strip():
                filled += 1
            else:
                missing += 1

        pct = round((filled / total_keys * 100), 1) if total_keys > 0 else 0.0
        if missing > 0 or total_keys == 0:
            perfect_parity = False

        lang_stats[lang] = {
            "filled": filled,
            "missing": missing,
            "coverage_percent": pct,
        }

    return {
        "file": str(path),
        "total_keys": total_keys,
        "languages": lang_stats,
        "perfect_parity": perfect_parity,
    }


def print_catalog_stats(stats: dict[str, Any]) -> None:
    """Formatiert und gibt die Statistiken als ASCII-Tabelle aus."""
    print("=================================================================")
    print(" CloudLockFixer - Tier-2 Übersetzungskatalog-Statistiken")
    print("=================================================================")
    print(f" Datei:             {stats['file']}")
    print(f" Inhaltsschlüssel:  {stats['total_keys']}")
    print("-----------------------------------------------------------------")
    print(" Sprache | Ausgefüllt | Fehlend | Abdeckung")
    print("---------+------------+---------+----------")
    for lang, s in stats["languages"].items():
        print(f"   {lang:<5} | {s['filled']:>10} | {s['missing']:>7} | {s['coverage_percent']:>6.1f} %")
    print("=================================================================")
    if stats["perfect_parity"]:
        print("[✓] 100% perfekte Parität über alle 6 Zielsprachen (Policy P-006 Tier-2 erfüllt).")
    else:
        print("[!] Warnung: Übersetzungskatalog weist unvollständige Zielsprachen auf.")


def find_german_strings(source_dir: Path | str) -> set[str]:
    """Scannt Quellcode nach deutschen GUI- und Dialog-Strings."""
    german_strings: set[str] = set()
    skip_dirs = {
        "build", "dist", "venv", ".venv", "__pycache__", "releases", ".git",
        "node_modules", "tools", "tests", ".pytest_temp",
    }

    for root, dirs, files in os.walk(str(source_dir)):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

                for pattern in STRING_PATTERNS:
                    for match in pattern.findall(content):
                        if match and is_german_hint(match):
                            german_strings.add(match.strip())

    return german_strings


def scan_and_update(source_dir: Path | str, trans_file: Path | str) -> dict[str, Any]:
    """Scannt Quelltexte und aktualisiert den Übersetzungskatalog atomar."""
    target_path = Path(trans_file)
    translations = load_translations(target_path)
    found = find_german_strings(source_dir)

    added = []
    upgraded = []

    for s in sorted(found):
        if s not in translations:
            entry = {"de": s}
            for lang in SUPPORTED_LANGUAGES:
                if lang != "de":
                    entry[lang] = ""
            translations[s] = entry
            added.append(s)
        else:
            entry = translations[s]
            if isinstance(entry, dict):
                for lang in SUPPORTED_LANGUAGES:
                    if lang not in entry:
                        entry[lang] = ""
                        if s not in upgraded:
                            upgraded.append(s)

    if added or upgraded:
        save_translations(target_path, translations)

    return {
        "added": added,
        "upgraded": upgraded,
        "total": len(translations),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstiegspunkt."""
    parser = argparse.ArgumentParser(
        description="CloudLockFixer Tier-2 Translation Management Tool & CI Gate (DE, EN, ES, ZH, JA, RU)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validiert strikte Parität über alle 6 Sprachen (Exit 0 bei Erfolg, Exit 1 bei Lücken).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Gibt detaillierte Statistiken und Abdeckungsgrade je Sprache aus.",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scannt Quelltexte nach neuen deutschen Strings und fügt sie dem Katalog hinzu.",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Projekt- oder Quellverzeichnis (Standard: Auto-Erkennung).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Gibt Statistiken als JSON aus.",
    )

    args = parser.parse_args(argv)
    trans_file = resolve_translation_file(args.dir)

    # 1. Paritätsprüfung (--check)
    if args.check:
        is_valid, findings = validate_catalog(trans_file)
        if not is_valid:
            print(f"[!] Paritätsprüfung FEHLGESCHLAGEN für {trans_file}:")
            for f in findings[:25]:
                print(f"    - {f}")
            if len(findings) > 25:
                print(f"    ... und {len(findings) - 25} weitere Befunde")
            return 1
        print(f"[✓] Paritätsprüfung BESTANDEN ({trans_file}): Alle 6 Sprachen vollständig synchron.")
        return 0

    # 2. Statistiken (--stats)
    if args.stats:
        stats = get_catalog_stats(trans_file)
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print_catalog_stats(stats)
        return 0 if stats.get("perfect_parity", False) else 1

    # 3. Quellcode-Scan (--scan)
    if args.scan:
        src_dir = Path(args.dir) if args.dir else Path(__file__).resolve().parent
        res = scan_and_update(src_dir, trans_file)
        print(f"[i] Scan abgeschlossen für {src_dir}:")
        print(f"    - {len(res['added'])} neue Strings hinzugefügt")
        print(f"    - {len(res['upgraded'])} bestehende Strings aktualisiert")
        print(f"    - {res['total']} Strings insgesamt in {trans_file}")
        return 0

    # Standard-Verhalten ohne Flags: Stats anzeigen
    stats = get_catalog_stats(trans_file)
    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print_catalog_stats(stats)
    return 0 if stats.get("perfect_parity", False) else 1


if __name__ == "__main__":
    sys.exit(main())
