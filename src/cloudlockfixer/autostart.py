"""Autostart via HKCU\\...\\Run (Windows)."""
from __future__ import annotations

import sys

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE = "CloudLockFixer"


def _launch_command() -> str:
    """Befehl, der die Tray-App startet (pythonw, kein Konsolenfenster)."""
    from .paths import launcher, pythonw
    return f'"{pythonw()}" "{launcher()}"'


def is_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            winreg.QueryValueEx(k, _VALUE)
            return True
    except OSError:
        return False


def enable() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, _VALUE, 0, winreg.REG_SZ, _launch_command())
        return True
    except OSError:
        return False


def disable() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, _VALUE)
        return True
    except OSError:
        return False
