"""Package-Fassade für das Translation-Management-Tooling von CloudLockFixer.

Ermöglicht sowohl direkten CLI-Aufruf über das Root-Skript als auch den programmatischen
Import über `cloudlockfixer.manage_translations`.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Sicherstellen, dass das Repo-Root für den Import des Hauptmoduls verfügbar ist
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from manage_translations import (  # noqa: E402
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    audit_catalog,
    find_german_strings,
    get_catalog_stats,
    is_german_hint,
    load_translations,
    main,
    print_catalog_stats,
    resolve_translation_file,
    save_translations,
    scan_and_update,
    validate_catalog,
)

__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "audit_catalog",
    "find_german_strings",
    "get_catalog_stats",
    "is_german_hint",
    "load_translations",
    "main",
    "print_catalog_stats",
    "resolve_translation_file",
    "save_translations",
    "scan_and_update",
    "validate_catalog",
]
