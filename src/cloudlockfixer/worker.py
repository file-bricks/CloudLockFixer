"""Worker: arbeitet die Queue ab.

Standard ist non-disruptiv: copy+delete funktioniert auch ohne den Sync-Client
zu beenden. Erst wenn ein Task mehrfach hängt (oder force_pause), wird der
zuständige Sync-Provider für den Lauf pausiert (M2) und danach wieder gestartet.
"""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .i18n import t as tr  # 't' ist unten die Task-Schleifenvariable
from .models import Queue, Task
from .ops import execute_chain
from .providers import SyncProvider, provider_for
from .settings import (
    DEFAULT_BACKOFF_BASE_SEC,
    DEFAULT_BACKOFF_MAX_SEC,
    DEFAULT_BACKOFF_MULTIPLIER,
    DEFAULT_MAX_RETRIES,
    DEFAULT_ON_PERMANENT_FAILURE,
    get_on_permanent_failure,
    load as load_settings,
)

log = logging.getLogger("clf")

ESCALATE_AFTER = 3  # ab so vielen Fehlversuchen den Sync-Client pausieren


def _record_permanent_failure(
    task: Task,
    data_dir: Path,
    hook_cmd_template: str | None = None,
) -> None:
    """Protokolliert einen permanent gescheiterten Task idempotent in failed.txt und führt den Hook aus."""
    if task.failure_reported:
        return

    step = task.chain[min(task.step_index, len(task.chain) - 1)] if task.chain else None
    op = step.op if step else ""
    src = step.src if step else ""
    dst = step.arg if step and step.op in ("move", "rename") else ""
    err = task.last_error or ""

    # 1. Fallback-Eintrag in failed.txt im Datenordner
    try:
        failed_file = data_dir / "failed.txt"
        now_str = datetime.now(timezone.utc).isoformat()
        line = (
            f"[{now_str}] task_id={task.id} status={task.status} "
            f"outcome={task.last_outcome} op={op} src={src} dst={dst} error={err}\n"
        )
        with failed_file.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        log.error("Failed to write to failed.txt: %s", e)

    # 2. Optionaler on_permanent_failure Hook
    if hook_cmd_template and hook_cmd_template.strip():
        try:
            cmd = hook_cmd_template
            replacements = {
                "{task_id}": task.id,
                "{op}": op,
                "{src}": src,
                "{dst}": dst,
                "{error}": err,
            }
            for placeholder, val in replacements.items():
                cmd = cmd.replace(placeholder, str(val))
            log.info("Executing on_permanent_failure hook for task %s", task.id)
            subprocess.run(cmd, shell=True, check=False, timeout=30)
        except Exception as exc:
            log.error("Failed executing on_permanent_failure hook for task %s: %s", task.id, exc)

    task.failure_reported = True


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
    backoff_base_sec: float = DEFAULT_BACKOFF_BASE_SEC,
    backoff_max_sec: float = DEFAULT_BACKOFF_MAX_SEC,
    backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    on_permanent_failure: str | None = None,
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

    if on_permanent_failure is None:
        try:
            on_permanent_failure = get_on_permanent_failure(load_settings())
        except Exception:
            on_permanent_failure = DEFAULT_ON_PERMANENT_FAILURE

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
    to_resume: list[SyncProvider] = []

    try:
        for prov in to_pause:
            # Client lief vor dem Pausierversuch -> muss im finally auf jeden Fall
            # wieder aufgenommen werden, selbst wenn pause() False zurückgab (z.B. 1,5s
            # Timeout bei langsamem Prozessende) oder der Prozess verzögert beendet wurde.
            to_resume.append(prov)
            try:
                if prov.pause():
                    summary["paused_providers"].append(prov.name)
                    log.info("Sync provider paused: %s", prov.name)
                else:
                    log.warning(
                        "Sync provider pause returned False (process may be exiting slowly): %s",
                        prov.name,
                    )
            except Exception as e:
                log.error("Exception while pausing sync provider %s: %s", prov.name, e)

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
                _record_permanent_failure(t, queue.data_dir, on_permanent_failure)
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
                _record_permanent_failure(t, queue.data_dir, on_permanent_failure)
            else:
                t.status = "pending"  # bleibt für nächsten Lauf
                t.last_outcome = "retryable"
                t.next_try_at = t.compute_next_retry(
                    base_sec=backoff_base_sec,
                    max_sec=backoff_max_sec,
                    multiplier=backoff_multiplier,
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
        for prov in to_resume:
            try:
                if prov.resume():
                    log.info("Sync provider resumed: %s", prov.name)
                else:
                    log.error("Failed to resume sync provider: %s", prov.name)
            except Exception as e:
                log.error("Exception while resuming sync provider %s: %s", prov.name, e)

    return summary
