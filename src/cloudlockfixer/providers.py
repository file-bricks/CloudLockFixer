"""Sync-Provider-Adapter (Windows). Nur das optionale Pausieren/Fortsetzen des
Sync-Clients ist providerspezifisch — der copy+delete-Kern funktioniert ohnehin
ohne Pause. OneDrive ist jetzt implementiert; weitere Provider sind vorgesehen
(YAGNI: erst bei Bedarf)."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path


class SyncProvider(ABC):
    name: str = "generic"

    @abstractmethod
    def owns_path(self, p: Path) -> bool: ...

    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def pause(self) -> bool: ...

    @abstractmethod
    def resume(self) -> bool: ...


def _is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


class OneDriveProvider(SyncProvider):
    name = "OneDrive"
    _exe_candidates = [
        Path(r"C:\Program Files\Microsoft OneDrive\OneDrive.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "OneDrive" / "OneDrive.exe",
    ]

    def _roots(self) -> list[Path]:
        roots: list[Path] = []
        for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            v = os.environ.get(key)
            if v:
                roots.append(Path(v))
        home_od = Path.home() / "OneDrive"
        if home_od.exists():
            roots.append(home_od)
        # de-dupe
        seen, out = set(), []
        for r in roots:
            rp = str(r).lower()
            if rp not in seen:
                seen.add(rp)
                out.append(r)
        return out

    def owns_path(self, p: Path) -> bool:
        p = Path(p)
        return any(_is_subpath(p, root) for root in self._roots())

    def is_running(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq OneDrive.exe", "/NH"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="ignore",
            ).stdout or ""
            return "OneDrive.exe" in out
        except (OSError, subprocess.SubprocessError):
            return False

    def pause(self) -> bool:
        """OneDrive beenden (M2). Echtes Pausieren bietet OneDrive nicht per CLI."""
        if sys.platform != "win32":
            return False
        try:
            subprocess.run(["taskkill", "/F", "/IM", "OneDrive.exe", "/T"],
                           capture_output=True, text=True, timeout=15,
                           encoding="utf-8", errors="ignore")
            time.sleep(1.5)
            return not self.is_running()
        except (OSError, subprocess.SubprocessError):
            return False

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


_PROVIDERS: list[SyncProvider] = [OneDriveProvider()]


def provider_for(path: Path | str) -> SyncProvider | None:
    """Liefert den Sync-Provider, der diesen Pfad besitzt — oder None."""
    p = Path(path)
    for prov in _PROVIDERS:
        try:
            if prov.owns_path(p):
                return prov
        except OSError:
            continue
    return None
