"""Worker: arbeitet die Queue ab.

Standard ist non-disruptiv: copy+delete funktioniert auch ohne den Sync-Client
zu beenden. Erst wenn ein Task mehrfach haengt (oder force_pause), wird der
zustaendige Sync-Provider fuer den Lauf pausiert (M2) und danach wieder gestartet.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import Queue, Task
from .ops import execute_chain
from .providers import SyncProvider, provider_for

log = logging.getLogger("clf")

ESCALATE_AFTER = 3  # ab so vielen Fehlversuchen den Sync-Client pausieren


def _task_paths(task: Task) -> list[Path]:
    out: list[Path] = []
    for s in task.chain:
        out.append(Path(s.src))
        if s.op == "move" and s.arg:
            out.append(Path(s.arg))
    return out


def _providers_to_pause(tasks: list[Task], force_pause: bool) -> set[SyncProvider]:
    provs: set[SyncProvider] = set()
    for t in tasks:
        if not force_pause and t.retry_count < ESCALATE_AFTER:
            continue
        for p in _task_paths(t):
            prov = provider_for(p)
            if prov is not None and prov.is_running():
                if prov.mount_type == "virtual":
                    log.warning("Skipping pause for %s (virtual mount)", prov.name)
                    continue
                provs.add(prov)
    return provs


def run_once(queue: Queue, force_pause: bool = False) -> dict:
    """Versucht alle offenen Tasks einmal. Gibt eine Ergebnis-Zusammenfassung."""
    queue.load()
    pending = queue.pending
    summary = {"pending_start": len(pending), "done": 0, "failed_again": 0,
               "paused_providers": []}
    if not pending:
        return summary

    to_pause = _providers_to_pause(pending, force_pause)
    paused: list[SyncProvider] = []
    for prov in to_pause:
        if prov.pause():
            paused.append(prov)
            summary["paused_providers"].append(prov.name)
            log.info("Sync provider paused: %s", prov.name)

    try:
        for t in pending:
            t.status = "running"
            t.retry_count += 1
            t.last_try = datetime.now(timezone.utc).isoformat()
            log.info("Task %s attempt %d: %s", t.id, t.retry_count, t.describe())
            if execute_chain(t):
                summary["done"] += 1
                log.info("Task %s completed.", t.id)
            else:
                t.status = "pending"  # bleibt fuer naechsten Lauf
                summary["failed_again"] += 1
                log.warning("Task %s still open: %s", t.id, t.last_error)
        queue.save()
    finally:
        for prov in paused:
            if prov.resume():
                log.info("Sync provider resumed: %s", prov.name)

    return summary
