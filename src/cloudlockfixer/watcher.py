"""Praeventiv-Waechter (P3, opt-in).

Beobachtet die Aenderungsrate in *konfigurierten* Ordnern (NICHT dem ganzen
OneDrive-Baum — das wuerde Online-only-Placeholder hydratisieren = ungewollte
Downloads). Bei hoher Aktivitaet wird der Sync-Client pausiert; nach einer
Ruhephase (Cooldown) wieder gestartet — so entstehen Locks gar nicht erst.

Die Entscheidungslogik (`decide`) ist rein/zustandsbehaftet und testbar; das
Zaehlen ist bounded + stat-only (liest nur Metadaten, hydratisiert nicht).
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from .providers import SyncProvider

log = logging.getLogger("clf")


class PreventiveWatcher:
    def __init__(
        self,
        provider: SyncProvider,
        *,
        watch_dirs: list[str] | None = None,
        threshold: int = 25,
        window_s: float = 15.0,
        cooldown_s: float = 90.0,
        scan_cap: int = 4000,
        time_fn=time.time,
    ):
        self.provider = provider
        self.watch_dirs = list(watch_dirs or [])
        self.threshold = threshold
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self.scan_cap = scan_cap
        self._time = time_fn
        self._paused_by_us = False
        self._last_activity: float | None = None

    # ── reine Entscheidung (testbar) ────────────────────────────────
    def decide(self, change_count: int) -> str:
        """'pause' | 'resume' | 'none'. Aktualisiert den internen Zustand."""
        now = self._time()
        if not self._paused_by_us:
            if change_count >= self.threshold:
                self._paused_by_us = True
                self._last_activity = now
                return "pause"
            return "none"
        # bereits von uns pausiert
        if change_count > 0:
            self._last_activity = now
            return "none"
        if self._last_activity is not None and now - self._last_activity >= self.cooldown_s:
            self._paused_by_us = False
            self._last_activity = None
            return "resume"
        return "none"

    # ── bounded, stat-only (hydratisiert NICHT) ─────────────────────
    def count_recent_changes(self) -> int:
        cutoff = self._time() - self.window_s
        n = scanned = 0
        for d in self.watch_dirs:
            root = Path(d)
            if not root.exists():
                continue
            try:
                for p in root.rglob("*"):
                    scanned += 1
                    if scanned > self.scan_cap:
                        return n
                    try:
                        if p.is_file() and p.stat().st_mtime >= cutoff:
                            n += 1
                    except OSError:
                        continue
            except OSError:
                continue
        return n

    def tick(self) -> str:
        action = self.decide(self.count_recent_changes())
        if action == "pause":
            if self.provider.is_running():
                self.provider.pause()
            else:
                self._paused_by_us = False
            log.info("Praeventiv-Waechter: %s pausiert (hohe Aenderungsrate).",
                     self.provider.name)
        elif action == "resume":
            self.provider.resume()
            log.info("Praeventiv-Waechter: %s wieder gestartet (Ruhe).",
                     self.provider.name)
        return action
