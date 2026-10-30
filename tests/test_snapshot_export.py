"""Tests für das Snapshot-Export-Modul und das CLI-Kommando `clf export-snapshot`."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cloudlockfixer import __version__, cli
from cloudlockfixer.models import Queue, Step, Task
from cloudlockfixer.snapshot import (
    SNAPSHOT_FILENAME,
    SNAPSHOT_SCHEMA_NAME,
    SNAPSHOT_SCHEMA_VERSION,
    build_snapshot,
    export_snapshot,
)


def test_build_snapshot_schema_and_metadata(tmp_path: Path):
    _ = Queue(tmp_path)
    snapshot = build_snapshot(tmp_path)

    assert snapshot["schema_name"] == SNAPSHOT_SCHEMA_NAME
    assert snapshot["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert "$schema" in snapshot
    assert "generated_at" in snapshot

    # App-Metadaten
    assert snapshot["app"]["name"] == "CloudLockFixer"
    assert snapshot["app"]["version"] == __version__
    assert snapshot["app"]["license"] == "MIT"

    # Environment
    assert "platform" in snapshot["environment"]
    assert "python_version" in snapshot["environment"]
    assert snapshot["environment"]["data_dir_name"] == tmp_path.name

    # Settings
    assert "interval_min" in snapshot["settings"]
    assert "backoff_base_sec" in snapshot["settings"]
    assert "backoff_multiplier" in snapshot["settings"]

    # Queue summary & Collections
    assert isinstance(snapshot["queue_summary"], dict)
    assert isinstance(snapshot["tasks"], list)
    assert isinstance(snapshot["providers"], list)


def test_build_snapshot_task_sanitization_and_due_state(tmp_path: Path):
    queue = Queue(tmp_path)

    now_utc = datetime.now(timezone.utc)
    future_time = (now_utc + timedelta(hours=2)).isoformat()

    # Task 1: Im Backoff (deferred)
    task1 = Task(
        chain=[Step(op="rename", src=str(tmp_path / "DocumentA.txt"), arg="DocumentB.txt")],
        next_try_at=future_time,
        retry_count=2,
        last_error="WinError 32: In use",
    )
    # Task 2: Fällig
    task2 = Task(
        chain=[Step(op="delete", src=str(tmp_path / "TempFile.log"))],
        retry_count=0,
    )
    # Task 3: Fehlgeschlagen
    task3 = Task(
        chain=[Step(op="move", src=str(tmp_path / "Src.dat"), arg=str(tmp_path / "Dst.dat"))],
        status="permanent_failed",
        retry_count=10,
        last_error="FileNotFoundError",
    )

    queue.add(task1)
    queue.add(task2)
    queue.add(task3)

    snapshot = build_snapshot(tmp_path)
    summary = snapshot["queue_summary"]

    assert summary["total"] == 3
    assert summary["pending"] == 2
    assert summary["deferred"] == 1
    assert summary["permanent_failed"] == 1

    tasks_by_id = {t["id"]: t for t in snapshot["tasks"]}
    s_task1 = tasks_by_id[task1.id]
    assert s_task1["is_due"] is False
    assert s_task1["retry_count"] == 2
    assert s_task1["steps"][0]["src_name"] == "DocumentA.txt"
    assert s_task1["steps"][0]["arg_display"] == "DocumentB.txt"

    s_task2 = tasks_by_id[task2.id]
    assert s_task2["is_due"] is True
    assert s_task2["steps"][0]["src_name"] == "TempFile.log"

    s_task3 = tasks_by_id[task3.id]
    assert s_task3["status"] == "permanent_failed"


def test_export_snapshot_creates_valid_file(tmp_path: Path):
    target = export_snapshot(data_dir=tmp_path)

    assert target.is_file()
    assert target.name == SNAPSHOT_FILENAME

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["schema_name"] == SNAPSHOT_SCHEMA_NAME
    assert data["app"]["version"] == __version__


def test_export_snapshot_custom_output_path(tmp_path: Path):
    custom_output = tmp_path / "exports" / "custom_snap.json"
    result = export_snapshot(data_dir=tmp_path, output_path=custom_output, pretty=True)

    assert result == custom_output
    assert custom_output.is_file()

    content = custom_output.read_text(encoding="utf-8")
    assert "\n" in content  # indentation check
    data = json.loads(content)
    assert data["schema_name"] == SNAPSHOT_SCHEMA_NAME


def test_cli_export_snapshot_command(tmp_path: Path, monkeypatch):
    out_file = tmp_path / "cli_snapshot.json"
    monkeypatch.setattr("cloudlockfixer.cli.data_dir", lambda: tmp_path)

    # Queue anlegen
    queue = Queue(tmp_path)
    queue.add(Task(chain=[Step(op="rename", src="test.txt", arg="test2.txt")]))

    ret = cli.main(["export-snapshot", "--output", str(out_file), "--pretty"])
    assert ret == 0
    assert out_file.is_file()

    content = out_file.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data["schema_name"] == SNAPSHOT_SCHEMA_NAME
    assert data["queue_summary"]["total"] == 1
