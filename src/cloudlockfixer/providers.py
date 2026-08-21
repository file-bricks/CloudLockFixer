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
import re
import string
import subprocess
import sys
import threading
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
        # Serialisiert pause()/resume() derselben Instanz zwischen Worker-Job-
        # und Watcher-Tick-Thread (FIX 4). RLock (reentrant), damit der Watcher
        # den Lock halten und darin pause()/resume() aufrufen kann.
        self._lock = threading.RLock()

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


def _gdrive_version_key(p: Path) -> tuple[int, ...]:
    """Semantischer Sortier-Schlüssel für versionierte GoogleDriveFS.exe-Pfade.

    Parst den Verzeichnisnamen des exe-Pfads als Integer-Tupel, damit z. B.
    '62.0.1' numerisch über '9.0.0' sortiert ('9' > '6' lexikografisch wäre falsch).
    Ungültige Komponenten werden auf (0,) normiert.
    """
    try:
        return tuple(int(x) for x in p.parent.name.split("."))
    except ValueError:
        return (0,)


def _check_process(exe_name: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="ignore",
        ).stdout or ""
        return exe_name.lower() in out.lower()
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


# Win32-Konstanten für die robuste Laufwerks-Abfrage.
_SEM_FAILCRITICALERRORS = 0x0001  # unterdrückt die "Kein Datenträger"-Dialogbox
_DRIVE_FIXED = 3
_DRIVE_REMOTE = 4

# Volume labels are user-visible strings and can be changed by the user.  A
# substring check would therefore classify e.g. ``"My Google Drive Backup"``
# as a virtual provider and could make the worker kill the wrong process.  The
# clients' known labels are matched exactly after harmless case/whitespace
# normalization; suffixes or prefixes remain non-matches.
_GOOGLE_DRIVE_VOLUME_LABELS = frozenset({"google drive"})
_PCLOUD_VOLUME_LABELS = frozenset({"pcloud drive"})


def _normalize_volume_label(label: str) -> str:
    """Normalize a Windows volume label without changing its meaning."""
    return " ".join(str(label).strip().casefold().split())


def _volume_label_matches(label: str, accepted: frozenset[str]) -> bool:
    """Return whether *label* is one of the provider's known exact labels."""
    return _normalize_volume_label(label) in accepted


def _get_volume_label(drive_letter: str) -> str:
    """Read volume label via Win32 API (no subprocess).

    Robust gegen nicht bereite Wechsel-/CD-Laufwerke: der Fehlermodus wird
    für die Dauer der Abfrage auf SEM_FAILCRITICALERRORS gesetzt (verhindert
    die blockierende "Kein Datenträger"-Dialogbox) und danach wiederhergestellt.
    Nur DRIVE_FIXED und DRIVE_REMOTE werden abgefragt — Cloud-Laufwerke
    (Google Drive, pCloud) mounten als FIXED oder REMOTE, während echte
    Wechseldatenträger/CD-ROMs übersprungen werden."""
    if sys.platform != "win32":
        return ""
    try:
        k = ctypes.windll.kernel32
        root = f"{drive_letter}:\\"
        old_mode = ctypes.c_uint(0)
        k.SetThreadErrorMode(_SEM_FAILCRITICALERRORS, ctypes.byref(old_mode))
        try:
            if k.GetDriveTypeW(root) not in (_DRIVE_FIXED, _DRIVE_REMOTE):
                return ""
            buf = ctypes.create_unicode_buffer(261)
            ok = k.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0)
            return buf.value if ok else ""
        finally:
            k.SetThreadErrorMode(old_mode.value, None)
    except (OSError, ValueError):
        return ""


def _read_box_custom_location() -> Path | None:
    """Read Box Drive's optional custom root parent from the Windows registry."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        return None

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Box\Box") as key:
            value, _ = winreg.QueryValueEx(key, "CustomBoxLocation")
    except (OSError, ValueError):
        return None

    if not isinstance(value, str):
        return None
    normalized = value.strip().strip('"')
    if not normalized:
        return None
    base = Path(normalized)
    return base if base.name.lower() == "box" else base / "Box"


def _extract_json_paths(node: object, key_names: set[str]) -> list[Path]:
    """Collect path-like strings for the given keys from nested JSON data."""
    paths: list[Path] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in key_names and isinstance(value, str):
                normalized = value.strip().strip('"').replace("/", os.sep)
                if normalized:
                    paths.append(Path(normalized))
            else:
                paths.extend(_extract_json_paths(value, key_names))
    elif isinstance(node, list):
        for item in node:
            paths.extend(_extract_json_paths(item, key_names))
    return paths


def _read_synology_custom_roots() -> list[Path]:
    """Read custom Synology sync roots from local config files if present.

    Synology's mass-deployment guide configures sync tasks via the field
    ``local_path``. The desktop client may materialize equivalent task config in
    its app-data directories; we scan small text config files there and accept
    only existing local paths. This keeps the default ``~/SynologyDrive`` path
    as fallback while allowing user-defined sync folders.
    """
    candidates: list[Path] = []
    base_dirs = [
        Path(os.environ.get("APPDATA", "")) / "SynologyDrive",
        Path(os.environ.get("LOCALAPPDATA", "")) / "SynologyDrive",
    ]
    key_names = {"local_path", "localPath"}
    line_re = re.compile(
        r"""(?ix)
        ["']?local(?:_|)path["']?
        \s*[:=]\s*
        ["'](?P<path>[a-z]:[\\/][^"']+)["']
        """
    )

    for base in base_dirs:
        if not base.exists():
            continue

        probe_dirs = [base]
        for name in ("config", "session", "data"):
            child = base / name
            if child.exists():
                probe_dirs.append(child)

        seen_files: set[str] = set()
        for folder in probe_dirs:
            for pattern in ("*.json", "*.conf", "*.cfg"):
                for cfg_path in folder.rglob(pattern):
                    if not cfg_path.is_file():
                        continue
                    key = str(cfg_path).lower()
                    if key in seen_files:
                        continue
                    seen_files.add(key)
                    try:
                        if cfg_path.stat().st_size > 1_000_000:
                            continue
                        raw = cfg_path.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue

                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        parsed = None
                    if parsed is not None:
                        candidates.extend(_extract_json_paths(parsed, key_names))

                    for match in line_re.finditer(raw):
                        normalized = match.group("path").strip().replace("/", os.sep)
                        if normalized:
                            candidates.append(Path(normalized))

    return _dedup_paths([p for p in candidates if p.exists()])


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
        with self._lock:
            return _kill_process("OneDrive.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        with self._lock:
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
    _RESUME_BASE: Path = Path(r"C:\Program Files\Google\Drive File Stream")

    def _detect_roots(self) -> list[Path]:
        if sys.platform != "win32":
            return []
        roots: list[Path] = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                label = _get_volume_label(letter)
                if _volume_label_matches(label, _GOOGLE_DRIVE_VOLUME_LABELS):
                    roots.append(Path(f"{letter}:\\"))
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("GoogleDriveFS.exe")

    def pause(self) -> bool:
        with self._lock:
            return _kill_process("GoogleDriveFS.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        base = self._RESUME_BASE
        if not base.exists():
            return False
        with self._lock:
            versions = sorted(base.glob("*/GoogleDriveFS.exe"),
                              key=_gdrive_version_key, reverse=True)
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
                if isinstance(data, dict):
                    for section in ("personal", "business"):
                        section_data = data.get(section)
                        if isinstance(section_data, dict):
                            path = section_data.get("path")
                            if path:
                                roots.append(Path(path))
            except (json.JSONDecodeError, OSError):
                pass
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("Dropbox.exe")

    def pause(self) -> bool:
        with self._lock:
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
        with self._lock:
            for exe in candidates:
                if exe.exists():
                    try:
                        subprocess.Popen([str(exe)])
                        return True
                    except OSError:
                        continue
            return False


# ── Box ────────────────────────────────────────────────────────────


class BoxProvider(SyncProvider):
    name = "Box"
    mount_type = "folder"

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        default_root = Path.home() / "Box"
        if default_root.exists():
            roots.append(default_root)

        custom_root = _read_box_custom_location()
        if custom_root and custom_root.exists():
            roots.append(custom_root)
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("Box.exe")

    def pause(self) -> bool:
        with self._lock:
            return _kill_process("Box.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(r"C:\Program Files\Box\Box\Box.exe"),
            Path(r"C:\Program Files (x86)\Box\Box\Box.exe"),
        ]
        with self._lock:
            for exe in candidates:
                if exe.exists():
                    try:
                        subprocess.Popen([str(exe)])
                        return True
                    except OSError:
                        continue
            return False


# ── Nextcloud ───────────────────────────────────────────────────────


class NextcloudProvider(SyncProvider):
    name = "Nextcloud"
    mount_type = "folder"

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        default_root = Path.home() / "Nextcloud"
        if default_root.exists():
            roots.append(default_root)

        cfg_path = Path(os.environ.get("APPDATA", "")) / "Nextcloud" / "nextcloud.cfg"
        if cfg_path.exists():
            try:
                for raw_line in cfg_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith(("#", ";")) or "localPath=" not in line:
                        continue
                    _, raw_path = line.split("localPath=", 1)
                    normalized = raw_path.strip().strip('"').replace("/", os.sep)
                    if normalized:
                        roots.append(Path(normalized))
            except OSError:
                pass
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("nextcloud.exe")

    def pause(self) -> bool:
        with self._lock:
            return _kill_process("nextcloud.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(r"C:\Program Files\Nextcloud\nextcloud.exe"),
            Path(r"C:\Program Files (x86)\Nextcloud\nextcloud.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Nextcloud" / "nextcloud.exe",
        ]
        with self._lock:
            for exe in candidates:
                if exe.exists():
                    try:
                        subprocess.Popen([str(exe)])
                        return True
                    except OSError:
                        continue
            return False


# ── pCloud ─────────────────────────────────────────────────────────


class PCloudProvider(SyncProvider):
    """pCloud Drive for Windows — virtueller Laufwerks-Mount.

    pCloud Drive erscheint unter Windows als Laufwerksbuchstabe, dessen
    Volume-Label "pCloud Drive" enthält. Erkennung analog zu Google Drive
    per GetVolumeInformationW (kein Subprocess nötig).
    """

    name = "pCloud"
    mount_type = "virtual"

    def _detect_roots(self) -> list[Path]:
        if sys.platform != "win32":
            return []
        roots: list[Path] = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                label = _get_volume_label(letter)
                if _volume_label_matches(label, _PCLOUD_VOLUME_LABELS):
                    roots.append(Path(f"{letter}:\\"))
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return _check_process("pCloud.exe")

    def pause(self) -> bool:
        with self._lock:
            return _kill_process("pCloud.exe")

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "pCloud" / "pCloud.exe",
            Path(r"C:\Program Files\pCloud\pCloud.exe"),
            Path(r"C:\Program Files (x86)\pCloud\pCloud.exe"),
        ]
        with self._lock:
            for exe in candidates:
                if exe.exists():
                    try:
                        subprocess.Popen([str(exe)])
                        return True
                    except OSError:
                        continue
            return False


# ── Synology Drive ─────────────────────────────────────────────────


class SynologyDriveProvider(SyncProvider):
    """Synology Drive Client for Windows.

    Offizieller Default-Root laut Synology-Mass-Deployment-Doku ist
    ``%USERPROFILE%\\SynologyDrive``. Resume startet die lokal installierte
    GUI-Binärdatei, die Synology unter ``%LOCALAPPDATA%\\SynologyDrive\\
    SynologyDrive.app\\bin\\cloud-drive-ui.exe`` ablegt.
    """

    name = "Synology Drive"
    mount_type = "folder"

    def _detect_roots(self) -> list[Path]:
        roots: list[Path] = []
        default_root = Path.home() / "SynologyDrive"
        if default_root.exists():
            roots.append(default_root)
        roots.extend(_read_synology_custom_roots())
        return _dedup_paths(roots)

    def is_running(self) -> bool:
        return (_check_process("cloud-drive-ui.exe")
                or _check_process("SynologyDrive.exe"))

    def pause(self) -> bool:
        with self._lock:
            ok1 = _kill_process("cloud-drive-ui.exe")
            ok2 = _kill_process("SynologyDrive.exe")
            return ok1 or ok2

    def resume(self) -> bool:
        if sys.platform != "win32":
            return False
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "SynologyDrive" / "SynologyDrive.app" / "bin" / "cloud-drive-ui.exe",
            Path(r"C:\Program Files\Synology\Synology Drive Client\cloud-drive-ui.exe"),
            Path(r"C:\Program Files (x86)\Synology\Synology Drive Client\cloud-drive-ui.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "SynologyDrive" / "SynologyDrive.app" / "bin" / "SynologyDrive.exe",
            Path(r"C:\Program Files\Synology\Synology Drive Client\SynologyDrive.exe"),
            Path(r"C:\Program Files (x86)\Synology\Synology Drive Client\SynologyDrive.exe"),
        ]
        with self._lock:
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
        with self._lock:
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
        with self._lock:
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
                  DropboxProvider(), BoxProvider(), NextcloudProvider(),
                  PCloudProvider(), SynologyDriveProvider(), ICloudProvider()]
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
