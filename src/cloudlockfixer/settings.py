"""Einstellungen (Intervall etc.) in data_dir/settings.json."""
from __future__ import annotations

import json

from .paths import data_dir

DEFAULT_INTERVAL_MIN = 120  # 2 h
# Cloud locks are normally temporary.  Keep the product's fire-and-forget
# contract unless a caller deliberately supplies a finite safety limit.
DEFAULT_MAX_RETRIES: int | None = None
DEFAULT_NOTIFICATIONS_ENABLED: bool = True


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
    return {
        "interval_min": DEFAULT_INTERVAL_MIN,
        "max_retries": DEFAULT_MAX_RETRIES,
        "notifications_enabled": DEFAULT_NOTIFICATIONS_ENABLED,
    }


def save(settings: dict) -> None:
    p = _path()
    try:
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(p)
    except OSError:
        pass


def resolve_language(cfg: dict) -> str:
    """Map stored "auto"/"de"/"en"/"es"/"zh"/"ja"/"ru" -> concrete language."""
    lang = cfg.get("language", "auto")
    if lang in ("de", "en", "es", "zh", "ja", "ru"):
        return lang
    from .i18n import detect_language
    return detect_language()


def get_max_retries(cfg: dict) -> int | None:
    """Return stored max_retries limit or DEFAULT_MAX_RETRIES (None = infinite)."""
    val = cfg.get("max_retries")
    if val is None or (isinstance(val, int) and val > 0 and not isinstance(val, bool)):
        return val
    return DEFAULT_MAX_RETRIES


def set_max_retries(cfg: dict, val: int | None) -> None:
    """Set and persist max_retries limit (None or positive int)."""
    if val is not None and (not isinstance(val, int) or val <= 0 or isinstance(val, bool)):
        raise ValueError("max_retries must be None or a positive integer")
    cfg["max_retries"] = val
    save(cfg)


def get_notifications_enabled(cfg: dict) -> bool:
    """Return whether desktop notifications / toasts are enabled."""
    return bool(cfg.get("notifications_enabled", DEFAULT_NOTIFICATIONS_ENABLED))


def set_notifications_enabled(cfg: dict, enabled: bool) -> None:
    """Set and persist whether desktop notifications / toasts are enabled."""
    cfg["notifications_enabled"] = bool(enabled)
    save(cfg)

