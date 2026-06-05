"""Einstellungen (Intervall etc.) in data_dir/settings.json."""
from __future__ import annotations

import json

from .paths import data_dir

DEFAULT_INTERVAL_MIN = 120  # 2 h


def _path():
    return data_dir() / "settings.json"


def load() -> dict:
    p = _path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (ValueError, OSError):
            # ValueError faengt JSONDecodeError UND UnicodeDecodeError (z.B.
            # abgebrochener Multibyte-Schreibvorgang, Disk-Korruption) ab.
            pass
    return {"interval_min": DEFAULT_INTERVAL_MIN}


def save(settings: dict) -> None:
    p = _path()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    tmp.replace(p)


def resolve_language(cfg: dict) -> str:
    """Map stored "auto"/"de"/"en" -> concrete "de"/"en"."""
    lang = cfg.get("language", "auto")
    if lang in ("de", "en"):
        return lang
    from .i18n import detect_language
    return detect_language()
