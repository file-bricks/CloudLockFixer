"""Einstellungen (Intervall etc.) in data_dir/settings.json."""
from __future__ import annotations

import json

from .paths import data_dir

DEFAULT_INTERVAL_MIN = 120  # 2 h
# Cloud locks are normally temporary.  Keep the product's fire-and-forget
# contract unless a caller deliberately supplies a finite safety limit.
DEFAULT_MAX_RETRIES: int | None = None
DEFAULT_NOTIFICATIONS_ENABLED: bool = True
DEFAULT_BACKOFF_BASE_SEC: int = 60  # Basis-Backoff: 60 s
DEFAULT_BACKOFF_MAX_SEC: int = 3600  # Maximaler Backoff: 1 h (3600 s)
DEFAULT_BACKOFF_MULTIPLIER: float = 2.0  # Verdopplung je Fehlversuch


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
        "backoff_base_sec": DEFAULT_BACKOFF_BASE_SEC,
        "backoff_max_sec": DEFAULT_BACKOFF_MAX_SEC,
        "backoff_multiplier": DEFAULT_BACKOFF_MULTIPLIER,
    }


def save(settings: dict) -> None:
    p = _path()
    tmp = p.with_suffix(".json.tmp")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(p)
    except OSError:
        pass
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def get_interval_min(cfg: dict) -> int:
    """Return stored interval_min in minutes or DEFAULT_INTERVAL_MIN."""
    val = cfg.get("interval_min")
    if isinstance(val, int) and val > 0 and not isinstance(val, bool):
        return val
    return DEFAULT_INTERVAL_MIN


def set_interval_min(cfg: dict, val: int) -> None:
    """Set and persist interval_min (positive integer in minutes)."""
    if not isinstance(val, int) or val <= 0 or isinstance(val, bool):
        raise ValueError("interval_min must be a positive integer")
    cfg["interval_min"] = val
    save(cfg)


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


def get_backoff_base(cfg: dict) -> int:
    """Return stored backoff_base_sec or DEFAULT_BACKOFF_BASE_SEC."""
    val = cfg.get("backoff_base_sec")
    if isinstance(val, int) and val > 0 and not isinstance(val, bool):
        return val
    return DEFAULT_BACKOFF_BASE_SEC


def set_backoff_base(cfg: dict, val: int) -> None:
    """Set and persist backoff_base_sec (positive integer in seconds)."""
    if not isinstance(val, int) or val <= 0 or isinstance(val, bool):
        raise ValueError("backoff_base_sec must be a positive integer")
    cfg["backoff_base_sec"] = val
    save(cfg)


def get_backoff_max(cfg: dict) -> int:
    """Return stored backoff_max_sec or DEFAULT_BACKOFF_MAX_SEC."""
    val = cfg.get("backoff_max_sec")
    if isinstance(val, int) and val > 0 and not isinstance(val, bool):
        return val
    return DEFAULT_BACKOFF_MAX_SEC


def set_backoff_max(cfg: dict, val: int) -> None:
    """Set and persist backoff_max_sec (positive integer in seconds)."""
    if not isinstance(val, int) or val <= 0 or isinstance(val, bool):
        raise ValueError("backoff_max_sec must be a positive integer")
    cfg["backoff_max_sec"] = val
    save(cfg)


def get_backoff_multiplier(cfg: dict) -> float:
    """Return stored backoff_multiplier (>= 1.0) or DEFAULT_BACKOFF_MULTIPLIER."""
    val = cfg.get("backoff_multiplier")
    if isinstance(val, (int, float)) and not isinstance(val, bool) and 1.0 <= val <= 100.0:
        return float(val)
    return DEFAULT_BACKOFF_MULTIPLIER


def set_backoff_multiplier(cfg: dict, val: float) -> None:
    """Set and persist backoff_multiplier (number between 1.0 and 100.0)."""
    if (not isinstance(val, (int, float)) or isinstance(val, bool)
            or not 1.0 <= val <= 100.0):
        raise ValueError("backoff_multiplier must be a number between 1.0 and 100.0")
    cfg["backoff_multiplier"] = float(val)
    save(cfg)
