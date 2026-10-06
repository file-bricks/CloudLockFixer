"""Plattformübergreifende Prozessmanagement-Abstraktion für CloudLockFixer (Task 169).

Kapselt Prozessprüfung, Beendigung und Start für Windows, macOS und Linux.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("clf")

# POSIX-Prozessnamen der Sync-Provider. Die Einträge werden EXAKT gegen den
# Prozessnamen geprüft (``pgrep -x`` / ``pkill -x`` bzw. /proc/<pid>/comm),
# nie als Teilstring der Kommandozeile: ``pkill -f box`` träfe sonst auch
# Dropbox, VirtualBox oder einen Editor, der ``~/Box/notiz.txt`` geöffnet hat.
_PROCESS_ALIASES_POSIX: dict[str, list[str]] = {
    "googledrivefs.exe": ["GoogleDriveFS", "Google Drive"],
    "onedrive.exe": ["OneDrive", "onedrive"],
    "dropbox.exe": ["Dropbox", "dropbox"],
    "box.exe": ["Box", "box"],
    "nextcloud.exe": ["nextcloud", "Nextcloud"],
    "pcloud.exe": ["pCloud", "pcloud"],
    "cloud-drive-ui.exe": ["cloud-drive-ui", "synology-drive", "Synology Drive"],
    "synologydrive.exe": ["SynologyDrive", "synology-drive", "Synology Drive"],
    "iclouddrive.exe": ["iCloudDrive", "bird", "cloudd"],
    "icloud.exe": ["iCloud", "bird", "cloudd"],
}


def get_posix_patterns(exe_name: str) -> list[str]:
    """Liefert POSIX-Suchmuster für ein Executable oder Alias."""
    key = exe_name.lower()
    if key in _PROCESS_ALIASES_POSIX:
        return list(_PROCESS_ALIASES_POSIX[key])
    if key.endswith(".exe"):
        return [exe_name[:-4]]
    return [exe_name]


# Linux kürzt den Prozessnamen (comm) auf 15 Zeichen; pgrep/pkill -x
# vergleichen gegen diesen gekürzten Namen.
_LINUX_COMM_MAX = 15


def _posix_match_name(pattern: str, platform: str) -> str:
    """Name, gegen den ``pgrep -x``/``pkill -x`` auf *platform* vergleichen."""
    if platform.startswith("linux"):
        return pattern[:_LINUX_COMM_MAX]
    return pattern


def _proc_names(entry: Any) -> set[str]:
    """Prozessnamen eines /proc/<pid>-Eintrags (comm und argv[0]-Basename)."""
    names: set[str] = set()
    try:
        comm = (entry / "comm").read_text(encoding="utf-8", errors="ignore").strip()
        if comm:
            names.add(comm.lower())
    except OSError:
        pass
    try:
        argv0 = (entry / "cmdline").read_bytes().split(b"\x00", 1)[0]
        base = argv0.decode("utf-8", errors="ignore").replace("\\", "/").rsplit("/", 1)[-1]
        if base:
            names.add(base.lower())
    except OSError:
        pass
    return names


def check_process(
    exe_name: str,
    *,
    _runner: Any = None,
    _path_cls: Any = None,
) -> bool:
    """Prüft plattformübergreifend, ob ein Prozess aktuell ausgeführt wird."""
    runner = _runner or subprocess.run
    path_cls = _path_cls or Path
    platform = sys.platform

    if platform == "win32":
        try:
            out = runner(
                ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore",
            ).stdout or ""
            return exe_name.lower() in out.lower()
        except (OSError, subprocess.SubprocessError):
            return False

    # Linux / macOS (POSIX)
    patterns = get_posix_patterns(exe_name)
    for pat in patterns:
        try:
            res = runner(
                ["pgrep", "-x", _posix_match_name(pat, platform)],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore",
            )
            if getattr(res, "returncode", 1) == 0 and (res.stdout or "").strip():
                return True
        except (OSError, subprocess.SubprocessError):
            pass

    # Fallback: /proc unter Linux prüfen falls verfügbar
    if platform.startswith("linux"):
        try:
            proc_dir = path_cls("/proc")
            if proc_dir.is_dir():
                wanted = {_posix_match_name(p, platform).lower() for p in patterns}
                wanted |= {p.lower() for p in patterns}
                for entry in proc_dir.iterdir():
                    if entry.is_dir() and entry.name.isdigit():
                        if _proc_names(entry) & wanted:
                            return True
        except (OSError, PermissionError):
            pass
    return False


def kill_process(
    exe_name: str,
    timeout: float = 15.0,
    sleep_delay: float = 1.5,
    *,
    _runner: Any = None,
    _sleep: Any = None,
    _checker: Any = None,
) -> bool:
    """Beendet einen Prozess plattformübergreifend und verifiziert die Beendigung."""
    runner = _runner or subprocess.run
    sleep_fn = _sleep or time.sleep
    checker_fn = _checker or check_process

    if sys.platform == "win32":
        try:
            runner(
                ["taskkill", "/F", "/IM", exe_name, "/T"],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
            )
            sleep_fn(sleep_delay)
            return not checker_fn(exe_name)
        except (OSError, subprocess.SubprocessError):
            return False

    # Linux / macOS (POSIX)
    patterns = get_posix_patterns(exe_name)
    for pat in patterns:
        try:
            runner(
                ["pkill", "-x", _posix_match_name(pat, sys.platform)],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
            )
        except (OSError, subprocess.SubprocessError):
            pass

    sleep_fn(sleep_delay)
    return not checker_fn(exe_name)


def launch_process(
    windows_candidates: list[Path] | None = None,
    windows_args: list[str] | None = None,
    macos_app: str | None = None,
    macos_args: list[str] | None = None,
    linux_commands: list[str | list[str]] | None = None,
    *,
    _popen: Any = None,
    _which: Any = None,
) -> bool:
    """Startet eine Applikation plattformabhängig (Windows, macOS via open, Linux via which)."""
    popen = _popen or subprocess.Popen
    which = _which or shutil.which

    if sys.platform == "win32":
        if not windows_candidates:
            return False
        extra = windows_args or []
        for exe in windows_candidates:
            if exe.exists():
                try:
                    popen([str(exe)] + extra)
                    return True
                except (OSError, subprocess.SubprocessError):
                    continue
        return False

    elif sys.platform == "darwin":
        if not macos_app:
            return False
        extra = macos_args or []
        cmd = ["open", "-a", macos_app] + extra
        try:
            popen(cmd)
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    else:
        # Linux
        if not linux_commands:
            return False
        for entry in linux_commands:
            if isinstance(entry, (list, tuple)):
                bin_name = entry[0]
                args = list(entry[1:])
            else:
                bin_name = entry
                args = []
            full_path = which(bin_name)
            if full_path:
                try:
                    popen([full_path] + args)
                    return True
                except (OSError, subprocess.SubprocessError):
                    continue
        return False


class ProcessManager:
    """Objektorientierte Abstraktion für Prozessüberwachung und -steuerung."""

    def __init__(self) -> None:
        pass

    def is_running(self, exe_name: str) -> bool:
        return check_process(exe_name)

    def terminate(self, exe_name: str, timeout: float = 15.0) -> bool:
        return kill_process(exe_name, timeout=timeout)

    def launch(
        self,
        windows_candidates: list[Path] | None = None,
        windows_args: list[str] | None = None,
        macos_app: str | None = None,
        macos_args: list[str] | None = None,
        linux_commands: list[str | list[str]] | None = None,
    ) -> bool:
        return launch_process(
            windows_candidates=windows_candidates,
            windows_args=windows_args,
            macos_app=macos_app,
            macos_args=macos_args,
            linux_commands=linux_commands,
        )
