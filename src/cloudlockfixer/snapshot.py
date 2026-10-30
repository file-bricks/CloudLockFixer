"""Snapshot-Export-Modul für CloudLockFixer (Schema cloudlockfixer-snapshot-v1).

Exportiert einen schreibgeschützten Snapshot des aktuellen System-, Queue-
und Provider-Zustands für den Web-Companion, mobile Endgeräte und externe
Diagnosetools ohne Offenlegung privater Anmeldeinformationen (Zero-Secrets).
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__, settings
from .models import Queue
from .paths import data_dir as get_data_dir
from .providers import available_providers

log = logging.getLogger("clf")

SNAPSHOT_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_SCHEMA_NAME = "cloudlockfixer-snapshot-v1"
SNAPSHOT_FILENAME = "cloudlockfixer-snapshot-v1.json"


def build_snapshot(data_dir: Path | None = None) -> dict[str, Any]:
    """Erzeugt ein vollständiges Snapshot-Dictionary gemäß Schema v1."""
    d_dir = data_dir or get_data_dir()
    queue = Queue(d_dir)
    queue.load()
    cfg = settings.load()

    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    # Queue-Statistiken
    tasks_list = []
    total = len(queue.tasks)
    pending_count = 0
    in_progress_count = 0
    deferred_count = 0
    failed_count = 0
    permanent_failed_count = 0
    done_count = 0

    for t in queue.tasks:
        if t.status == "pending":
            pending_count += 1
            if not t.is_due(now_utc):
                deferred_count += 1
        elif t.status == "running":
            in_progress_count += 1
        elif t.status == "failed":
            failed_count += 1
        elif t.status == "permanent_failed":
            permanent_failed_count += 1
        elif t.status == "done":
            done_count += 1

        steps_data = []
        for s in t.chain:
            src_p = Path(s.src)
            steps_data.append({
                "op": s.op,
                "src_name": src_p.name or s.src,
                "src_display": str(s.src),
                "arg_display": s.arg if s.arg is not None else "",
            })

        tasks_list.append({
            "id": t.id,
            "status": t.status,
            "retry_count": t.retry_count,
            "created_at": t.created_at,
            "last_try": t.last_try,
            "last_error": t.last_error,
            "last_outcome": t.last_outcome,
            "step_index": t.step_index,
            "next_try_at": t.next_try_at,
            "is_due": t.is_due(now_utc),
            "steps": steps_data,
        })

    # Provider-Status
    providers_list = []
    try:
        all_provs = available_providers()
        for p in all_provs:
            try:
                roots = p._roots()
                roots_count = len(roots)
            except Exception:
                roots_count = 0
            try:
                running = p.is_running()
            except Exception:
                running = False
            providers_list.append({
                "name": p.name,
                "mount_type": getattr(p, "mount_type", "folder"),
                "is_running": running,
                "roots_count": roots_count,
            })
    except Exception as exc:
        log.warning("Fehler beim Ermitteln der Provider für Snapshot: %s", exc)

    return {
        "$schema": "https://schemas.file-bricks.org/cloudlockfixer/snapshot-v1.json",
        "schema_name": SNAPSHOT_SCHEMA_NAME,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "generated_at": now_iso,
        "app": {
            "name": "CloudLockFixer",
            "version": __version__,
            "license": "MIT",
            "homepage": "https://github.com/file-bricks/CloudLockFixer",
        },
        "environment": {
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "data_dir_name": d_dir.name,
        },
        "settings": {
            "interval_min": settings.get_interval_min(cfg),
            "max_retries": settings.get_max_retries(cfg),
            "notifications_enabled": settings.get_notifications_enabled(cfg),
            "language": settings.resolve_language(cfg),
            "backoff_base_sec": settings.get_backoff_base(cfg),
            "backoff_max_sec": settings.get_backoff_max(cfg),
            "backoff_multiplier": settings.get_backoff_multiplier(cfg),
        },
        "queue_summary": {
            "total": total,
            "pending": pending_count,
            "in_progress": in_progress_count,
            "deferred": deferred_count,
            "failed": failed_count,
            "permanent_failed": permanent_failed_count,
            "done": done_count,
        },
        "tasks": tasks_list,
        "providers": providers_list,
    }


def export_snapshot(
    data_dir: Path | None = None,
    output_path: Path | str | None = None,
    pretty: bool = True,
) -> Path:
    """Schreibt den Snapshot atomar in eine JSON-Datei."""
    d_dir = data_dir or get_data_dir()
    if output_path is None:
        target = d_dir / SNAPSHOT_FILENAME
    else:
        target = Path(output_path).resolve()

    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot_data = build_snapshot(d_dir)
    json_bytes = json.dumps(
        snapshot_data,
        ensure_ascii=False,
        indent=2 if pretty else None,
    ).encode("utf-8")

    # Atomares Schreiben via Staging-Datei im selben Verzeichnis
    tmp_path = target.with_suffix(".tmp")
    try:
        tmp_path.write_bytes(json_bytes)
        try:
            os.replace(tmp_path, target)
        except PermissionError:
            import time
            time.sleep(0.05)
            os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
        target.write_bytes(json_bytes)

    log.info("Snapshot erfolgreich exportiert nach: %s", target)
    return target
