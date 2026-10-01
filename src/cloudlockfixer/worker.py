"""Worker: arbeitet die Queue ab.

Standard ist non-disruptiv: copy+delete funktioniert auch ohne den Sync-Client
zu beenden. Erst wenn ein Task mehrfach hängt (oder force_pause), wird der
zuständige Sync-Provider für den Lauf pausiert (M2) und danach wieder gestartet.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from .i18n import t as tr  # 't' ist unten die Task-Schleifenvariable
from .models import Queue, Task
from .ops import execute_chain
from .providers import SyncProvider, provider_for
from .settings import (
    DEFAULT_BACKOFF_BASE_SEC,
    DEFAULT_BACKOFF_MAX_SEC,
    DEFAULT_MAX_RETRIES,
)

log = logging.getLogger("clf")

ESCALATE_AFTER = 3  # ab so vielen Fehlversuchen den Sync-Client pausieren


def _task_paths(task: Task) -> list[Path]:
    if task.step_index >= len(task.chain):
        return []

    s = task.chain[task.step_index]
    if s.op not in ("rename", "move", "delete"):
        return []
    if not s.src or not s.src.strip() or s.src.strip() in (".", "./", ".\\"):
        return []
    if s.op == "rename" and (not s.arg or not s.arg.strip() or s.arg.strip() in (".", "..") or "/" in s.arg or "\\" in s.arg):
        return []
    if s.op == "move" and (not s.arg or not s.arg.strip() or s.arg.strip() in (".", "./", ".\\")):
        return []

    src = Path(s.src)
    try:
        src.lstat()
    except (FileNotFoundError, NotADirectoryError):
        # Eine Provider-Pause kann einen fehlenden Quellpfad nicht reparieren.
        # Der echte Ausführungspfad entscheidet danach race-sicher zwischen
        # idempotentem Erfolg und terminaler Blockierung.
        return []
    except OSError:
        # Bei unklarem Dateisystemzustand bleibt die bisherige Eskalation aktiv.
        pass

    out = [src]
    if s.op == "move" and s.arg:
        out.append(Path(s.arg))
    return out


def _providers_to_pause(
    tasks: list[Task],
    force_pause: bool,
    apply_backoff: bool = False,
    ignore_backoff: bool | None = None,
) -> set[SyncProvider]:
    if ignore_backoff is not None:
        apply_backoff = not ignore_backoff
    provs: set[SyncProvider] = set()
    for t in tasks:
        if apply_backoff and not t.is_due():
            continue
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


def run_once(
    queue: Queue,
    force_pause: bool = False,
    max_retries: int | None = DEFAULT_MAX_RETRIES,
    apply_backoff: bool = False,
    ignore_backoff: bool | None = None,
    backoff_base_sec: int = DEFAULT_BACKOFF_BASE_SEC,
    backoff_max_sec: int = DEFAULT_BACKOFF_MAX_SEC,
) -> dict:
    """Versucht alle offenen Tasks einmal. Gibt eine Ergebnis-Zusammenfassung.

    Ohne explizites Limit bleiben fehlgeschlagene Tasks pending und werden bei
    späteren Läufen erneut versucht. Ein positiver, endlicher ``max_retries``
    kann für aufruferspezifische Sicherheitsgrenzen weiterhin gesetzt werden.
    Wiederholungsversuche unterliegen bei ``apply_backoff=True`` einem gedeckelten
    exponentiellen Backoff.
    """
    if ignore_backoff is not None:
        apply_backoff = not ignore_backoff

    queue.load()
    pending = queue.pending
    summary = {
        "pending_start": len(pending),
        "done": 0,
        "failed_again": 0,
        "failed_permanent": 0,
        "blocked": 0,
        "deferred": 0,
        "paused_providers": [],
    }
    if not pending:
        return summary

    to_pause = _providers_to_pause(pending, force_pause, apply_backoff=apply_backoff)
    paused: list[SyncProvider] = []
    for prov in to_pause:
        if prov.pause():
            paused.append(prov)
            summary["paused_providers"].append(prov.name)
            log.info("Sync provider paused: %s", prov.name)

    try:
        for t in pending:
            if apply_backoff and not t.is_due():
                summary["deferred"] += 1
                log.debug("Task %s deferred until %s (backoff)", t.id, t.next_try_at)
                continue

            t.status = "running"
            t.retry_count += 1
            t.last_try = datetime.now(timezone.utc).isoformat()
            log.info("Task %s attempt %d: %s", t.id, t.retry_count, t.describe())
            if execute_chain(t):
                t.next_try_at = ""
                summary["done"] += 1
                log.info("Task %s completed.", t.id)
            elif t.last_outcome == "blocked":
                t.status = "blocked"
                t.next_try_at = ""
                summary["blocked"] += 1
                log.error("Task %s blocked: %s", t.id, t.last_error)
            elif max_retries is not None and t.retry_count >= max_retries:
                t.status = "failed"
                t.last_outcome = "permanent"
                t.next_try_at = ""
                t.last_error = tr(
                    "task_failed_max_retries",
                    n=t.retry_count,
                    err=t.last_error or tr("task_failed_unknown_error"),
                )
                summary["failed_permanent"] += 1
                log.error(
                    "Task %s failed permanently after %d attempts: %s",
                    t.id,
                    t.retry_count,
                    t.last_error,
                )
            else:
                t.status = "pending"  # bleibt für nächsten Lauf
                t.last_outcome = "retryable"
                t.next_try_at = t.compute_next_retry(
                    base_sec=backoff_base_sec, max_sec=backoff_max_sec
                )
                summary["failed_again"] += 1
                log.warning(
                    "Task %s still open (next retry at %s): %s",
                    t.id,
                    t.next_try_at,
                    t.last_error,
                )
        queue.save()
    finally:
        for prov in paused:
            if prov.resume():
                log.info("Sync provider resumed: %s", prov.name)

    return summary
