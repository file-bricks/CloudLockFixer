"""Sync-Provider-Adapter (Windows). Der copy+delete-Kern funktioniert ohne
Pause — das Pausieren ist nur die Eskalationsstufe nach mehreren Fehlversuchen.

Provider werden lazy per Auto-Discovery erkannt: installierte Clients
mit erkennbaren Root-Pfaden werden in _PROVIDERS aufgenommen. Roots werden
pro Instanz einmal ermittelt und gecacht (kein wiederholtes wmic/ctypes)."""
from __future__ import annotations

import ctypes
import json
import logging
import os
import string
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path

log = logging.getLogger("clf")

WATCHER_TICK_MS = 15_000


class SyncProvider(ABC):
    name: str = "generic"
    mount_type: str = "folder"

    def __init__(self) -> None:
        self._cached_roots: list[Path] | None = None

    @abstractmethod
    def _detect_roots(self) -> list[Path]: ...

    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def pause(self) -> bool: ...

    @abstractmethod
    def resume(self) -> bool: ...

    def _roots(self) -> list[Path]:
        if self._cached_roots is None:
            self._cached_roots = self._detect_roots()
        return self._cached_roots

    def owns_path(self, p: Path) -> bool:
        return any(_is_subpath(Path(p), root) for root in self._roots())


def _is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _dedup_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _check_process(exe_name: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="ignore",
        ).stdout or ""
        return exe_name in out
    except (OSError, subprocess.SubprocessError):
        return False


def _kill_process(exe_name: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        subprocess.run(["taskkill", "/F", "/IM", exe_name, "/T"],
                       capture_output=True, text=True, timeout=15,
                       encoding="utf-8", errors="ignore")
        time.sleep(1.5)
        return not _check_process(exe_name)
    except (OSError, subprocess.SubprocessError):
        return False


def _get_volume_label(drive_letter: str) -> str:
    """Read volume label via Win32 API (no subprocess)."""
    if sys.platform != "win32":
        return ""
    buf = ctypes.create_unicode_buffer(261)
    try:
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            f"{drive_letter}:\\", buf, 261,
            None, None, None, None, 0,
        )
        return buf.value if ok else ""
    except (OSError, ValueError):
        return ""


# ── OneDrive ───────────────────────────────────────────────────────


class OneDriveProvider(SyncProvider):
    name = "OneDrive"
    mount_type = "folder"
    _exe_candidates = [
        Path(r"C:\Program Files\Microsoft OneDrive\OneDrive.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "OneDrive" / "OneDrive.exe",
    ]

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            v = os.environ.get(key)
            if v:
                roots.append(Path(v))
        home_od = Path.home() / "OneDrive"
        if home_od.exists():
            roots.append(home_od)
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("OneDrive.exe")

    def pause(self) -> bool:
        return _kill_process("OneDrive.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        for exe in self._exe_candidates:
            if exe.exists():
                try:
                    subprocess.Popen([str(exe), "/background"])
                    return True
                except OSError:
                    continue
        return False


# ── Google Drive ───────────────────────────────────────────────────


class GoogleDriveProvider(SyncProvider):
    name = "Google Drive"
    mount_type = "virtual"

    def _detect_roots(self) -> list[Path]:
        if sys.platform != "win32":
            return []
        roots: list[Path] = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                label = _get_volume_label(letter)
                if "Google Drive" in label:
                    roots.append(Path(f"{letter}:\\"))
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("GoogleDriveFS.exe")

    def pause(self) -> bool:
        return _kill_process("GoogleDriveFS.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        base = Path(r"C:\Program Files\Google\Drive File Stream")
        if not base.exists():
            return False
        versions = sorted(base.glob("*/GoogleDriveFS.exe"), reverse=True)
        for exe in versions:
            try:
                subprocess.Popen([str(exe)])
                return True
            except OSError:
                continue
        return False


# ── Dropbox ────────────────────────────────────────────────────────


class DropboxProvider(SyncProvider):
    name = "Dropbox"
    mount_type = "folder"

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        home_db = Path.home() / "Dropbox"
        if home_db.exists():
            roots.append(home_db)
        info_json = Path(os.environ.get("APPDATA", "")) / "Dropbox" / "info.json"
        if info_json.exists():
            try:
                data = json.loads(info_json.read_text(encoding="utf-8"))
                for section in ("personal", "business"):
                    path = data.get(section, {}).get("path")
                    if path:
                        roots.append(Path(path))
            except (json.JSONDecodeError, OSError):
                pass
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("Dropbox.exe")

    def pause(self) -> bool:
        return _kill_process("Dropbox.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Dropbox" / "Dropbox.exe",
            Path(os.environ.get("APPDATA", "")) / "Dropbox" / "bin" / "Dropbox.exe",
            Path(r"C:\Program Files\Dropbox\Client\Dropbox.exe"),
            Path(r"C:\Program Files (x86)\Dropbox\Client\Dropbox.exe"),
        ]
        for exe in candidates:
            if exe.exists():
                try:
                    subprocess.Popen([str(exe)])
                    return True
                except OSError:
                    continue
        return False


# ── iCloud ─────────────────────────────────────────────────────────


class ICloudProvider(SyncProvider):
    name = "iCloud"
    mount_type = "folder"

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        for name in ("iCloudDrive", "iCloud Drive"):
            p = Path.home() / name
            if p.exists():
                roots.append(p)
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return (_check_process("iCloudDrive.exe")
                or _check_process("iCloud.exe"))

    def pause(self) -> bool:
        ok1 = _kill_process("iCloudDrive.exe")
        ok2 = _kill_process("iCloud.exe")
        return ok1 or ok2

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(r"C:\Program Files\iCloud\iCloudDrive.exe"),
            Path(r"C:\Program Files (x86)\iCloud\iCloudDrive.exe"),
            Path(r"C:\Program Files\Common Files\Apple\Internet Services\iCloudDrive.exe"),
        ]
        for exe in candidates:
            if exe.exists():
                try:
                    subprocess.Popen([str(exe)])
                    return True
                except OSError:
                    continue
        return False


# ── Lazy Auto-Discovery ───────────────────────────────────────────


def _discover_providers() -> list[SyncProvider]:
    candidates = [OneDriveProvider(), GoogleDriveProvider(),
                  DropboxProvider(), ICloudProvider()]
    active: list[SyncProvider] = []
    for prov in candidates:
        try:
            if prov._roots():
                active.append(prov)
        except Exception:
            continue
    return active if active else [OneDriveProvider()]


_PROVIDERS: list[SyncProvider] | None = None


def _get_providers() -> list[SyncProvider]:
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = _discover_providers()
    return _PROVIDERS


def available_providers() -> list[SyncProvider]:
    return list(_get_providers())


def provider_for(path: Path | str) -> SyncProvider | None:
    p = Path(path)
    for prov in _get_providers():
        try:
            if prov.owns_path(p):
                return prov
        except OSError:
            continue
    return None
