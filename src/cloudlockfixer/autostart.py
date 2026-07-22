"""Autostart integration for Windows, Linux and macOS desktop sessions."""
from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE = "CloudLockFixer"
_LINUX_DESKTOP_FILE = "cloudlockfixer.desktop"
_MACOS_LAUNCH_AGENT_FILE = "com.cloudlockfixer.agent.plist"
_MACOS_LAUNCH_AGENT_LABEL = "com.cloudlockfixer.agent"


def _launch_args() -> tuple[str, ...]:
    if getattr(sys, "frozen", False):
        return (sys.executable,)
    from .paths import launcher, pythonw

    return (pythonw(), str(launcher()))


def _launch_command() -> str:
    """Befehl, der die Tray-App startet (pythonw, kein Konsolenfenster)."""
    return " ".join(f'"{arg}"' for arg in _launch_args())


def _desktop_quote(value: str) -> str:
    """Quote one argument according to the Desktop Entry Exec field rules."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace(chr(96), "\\" + chr(96))
        .replace("$", "\\$")
        .replace("%", "%%")
    )
    return f'"{escaped}"'


def _desktop_exec_command() -> str:
    return " ".join(_desktop_quote(arg) for arg in _launch_args())


def _linux_desktop_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "autostart" / _LINUX_DESKTOP_FILE


def _linux_desktop_entry() -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        "Name=CloudLockFixer\n"
        "Comment=Run delayed cloud file operations\n"
        f"Exec={_desktop_exec_command()}\n"
        "Terminal=false\n"
        "Hidden=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def _linux_is_enabled() -> bool:
    try:
        lines = set(_linux_desktop_path().read_text(encoding="utf-8").splitlines())
    except OSError:
        return False

    required = {
        "[Desktop Entry]",
        "Type=Application",
        f"Exec={_desktop_exec_command()}",
        "Terminal=false",
        "Hidden=false",
        "X-GNOME-Autostart-enabled=true",
    }
    return required.issubset(lines)


def _linux_enable() -> bool:
    target = _linux_desktop_path()
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(_linux_desktop_entry(), encoding="utf-8", newline="\n")
        temporary.replace(target)
        target.chmod(0o644)
        return True
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _linux_disable() -> bool:
    try:
        _linux_desktop_path().unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _macos_launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / _MACOS_LAUNCH_AGENT_FILE


def _macos_launch_agent_payload() -> dict[str, object]:
    return {
        "Label": _MACOS_LAUNCH_AGENT_LABEL,
        "ProgramArguments": list(_launch_args()),
        "RunAtLoad": True,
        "KeepAlive": False,
    }


def _macos_is_enabled() -> bool:
    try:
        with _macos_launch_agent_path().open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return False
    return payload == _macos_launch_agent_payload()


def _macos_enable() -> bool:
    target = _macos_launch_agent_path()
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(
            plistlib.dumps(
                _macos_launch_agent_payload(),
                fmt=plistlib.FMT_XML,
                sort_keys=True,
            )
        )
        temporary.replace(target)
        target.chmod(0o644)
        return True
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _macos_disable() -> bool:
    try:
        _macos_launch_agent_path().unlink(missing_ok=True)
        return True
    except OSError:
        return False


def is_enabled() -> bool:
    if sys.platform.startswith("linux"):
        return _linux_is_enabled()
    if sys.platform == "darwin":
        return _macos_is_enabled()
    if sys.platform != "win32":
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.QueryValueEx(key, _VALUE)
            return True
    except OSError:
        return False


def enable() -> bool:
    if sys.platform.startswith("linux"):
        return _linux_enable()
    if sys.platform == "darwin":
        return _macos_enable()
    if sys.platform != "win32":
        return False

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, _VALUE, 0, winreg.REG_SZ, _launch_command())
        return True
    except OSError:
        return False


def disable() -> bool:
    if sys.platform.startswith("linux"):
        return _linux_disable()
    if sys.platform == "darwin":
        return _macos_disable()
    if sys.platform != "win32":
        return False

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, _VALUE)
        return True
    except OSError:
        return False
