"""manage_translations.py - Tier-2 i18n Auto-Scanner und Konsistenzprüfer.
=======================================================================
Verwaltet und auditiert Übersetzungskataloge für CloudLockFixer gemäß
Policy P-006 Tier-2 (DE, EN, ES, ZH, JA, RU).

Verwendung:
    python manage_translations.py [--dir PROJEKTVERZEICHNIS] [--check] [--export-json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Sicherstellen, dass UTF-8-Ausgabe unter Windows PowerShell sauber funktioniert
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cloudlockfixer.i18n import (  # noqa: E402
    _CATALOG,
    SUPPORTED_LANGUAGES,
    export_catalog_json,
)

TRANSLATION_FILE = PROJECT_ROOT / "locales" / "translations.json"

STRING_PATTERNS = [
    re.compile(r'\bt\(\s*["\']([^"\']+)["\']'),
    re.compile(r'text\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'setText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'setWindowTitle\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'setToolTip\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QLabel\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QPushButton\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'addAction\s*\([^,]*["\']([^"\']+)["\']\s*\)'),
]

GERMAN_HINTS = [
    "datei", "ordner", "fehler", "laden", "speichern",
    "ansicht", "optionen", "zurueck", "anzeigen", "export",
    "beenden", "einstellungen", "abbrechen", "hilfe", "löschen",
    "umbenennen", "verschieben", "warteschlange", "sperre", "wiederholen",
]


def is_german(text: str) -> bool:
    """Heuristik zur Erkennung deutscher Strings."""
    if any(ch in text for ch in "äöüÄÖÜß"):
        return True
    text_lower = text.lower()
    return any(w in text_lower for w in GERMAN_HINTS)


def find_used_t_keys(source_dir: Path) -> set[str]:
    """Findet alle Schlüssel, die im Python-Code via t(...) aufgerufen werden."""
    t_pattern = re.compile(r'\bt\(\s*["\']([^"\']+)["\']')
    found_keys: set[str] = set()
    skip_dirs = {"build", "dist", "venv", ".venv", "__pycache__", ".git", "tests"}

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                for match in t_pattern.findall(content):
                    found_keys.add(match.strip())
    return found_keys


def audit_catalog(check_mode: bool = False) -> int:
    """Prüft Vollständigkeit und Parität des Katalogs über alle 6 Sprachen."""
    errors = 0
    total_keys = len(_CATALOG)
    print(f"[i] Katalog-Prüfung: {total_keys} Schlüssel in src/cloudlockfixer/i18n.py")

    # 1. Paritätsprüfung über alle 6 Zielsprachen
    for key, trans in _CATALOG.items():
        for lang in SUPPORTED_LANGUAGES:
            val = trans.get(lang)
            if val is None or not str(val).strip():
                print(f"[FAIL] Schlüssel '{key}' fehlt Übersetzung für Sprache '{lang}'")
                errors += 1

    # 2. Prüfen, ob verwendete t()-Keys im Katalog existieren
    src_dir = PROJECT_ROOT / "src" / "cloudlockfixer"
    used_keys = find_used_t_keys(src_dir)
    for k in sorted(used_keys):
        if k not in _CATALOG:
            print(f"[FAIL] t('{k}') im Quelltext verwendet, aber nicht in _CATALOG definiert")
            errors += 1

    # 3. JSON-Spiegel prüfen / synchronisieren
    if TRANSLATION_FILE.is_file():
        try:
            with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            if len(json_data) != total_keys:
                print(f"[WARN] locales/translations.json hat {len(json_data)} Keys, _CATALOG hat {total_keys}")
                if check_mode:
                    errors += 1
        except Exception as exc:
            print(f"[FAIL] Fehler beim Lesen von {TRANSLATION_FILE}: {exc}")
            errors += 1
    else:
        print(f"[WARN] {TRANSLATION_FILE} existiert nicht")
        if check_mode:
            errors += 1

    if not check_mode:
        exported = export_catalog_json(TRANSLATION_FILE)
        print(f"[+] locales/translations.json erfolgreich aktualisiert ({exported})")

    if errors == 0:
        print(f"[OK] 100% Parität über alle {len(SUPPORTED_LANGUAGES)} Sprachen ({', '.join(SUPPORTED_LANGUAGES)}).")
        return 0
    else:
        print(f"[FAIL] {errors} Konsistenzfehler im Übersetzungskatalog gefunden.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="CloudLockFixer Tier-2 i18n Management")
    parser.add_argument("--check", action="store_true", help="CI-Prüfmodus: Nicht-Null-Exit bei Lücken")
    parser.add_argument("--export-json", action="store_true", help="locales/translations.json aktualisieren")
    parser.add_argument("--dir", default=str(PROJECT_ROOT), help="Projektverzeichnis (Default: Repo-Root)")

    args = parser.parse_args()
    return audit_catalog(check_mode=args.check)


if __name__ == "__main__":
    sys.exit(main())
