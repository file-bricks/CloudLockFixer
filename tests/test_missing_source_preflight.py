"""Regressionen für terminal fehlende Queue-Quellen."""
from __future__ import annotations

import json
from unittest.mock import patch

from cloudlockfixer.models import Queue, Step, Task
from cloudlockfixer.ops import execute_chain
from cloudlockfixer.worker import run_once


class FakeProvider:
    name = "FakeDrive"
    mount_type = "folder"

    def __init__(self) -> None:
        self.pause_calls = 0
        self.resume_calls = 0

    def is_running(self) -> bool:
        return True

    def pause(self) -> bool:
        self.pause_calls += 1
        return True

    def resume(self) -> bool:
        self.resume_calls += 1
        return True


def test_legacy_missing_move_source_blocks_before_provider_pause(tmp_path):
    """Ein alter Endlos-Task wird ohne Pause einmalig auf blocked migriert."""
    data_dir = tmp_path / "queue"
    data_dir.mkdir()
    src = tmp_path / "missing.txt"
    dst = tmp_path / "target.txt"
    payload = {
        "version": 1,
        "tasks": [{
            "id": "legacy01",
            "status": "pending",
            "retry_count": 439,
            "chain": [{"op": "move", "src": str(src), "arg": str(dst)}],
        }],
    }
    (data_dir / "queue.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    queue = Queue(data_dir)
    provider = FakeProvider()

    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        first = run_once(queue, force_pause=True)

    stored = queue.tasks[0]
    assert first["blocked"] == 1
    assert first["paused_providers"] == []
    assert provider.pause_calls == 0
    assert provider.resume_calls == 0
    assert stored.status == "blocked"
    assert stored.last_outcome == "blocked"
    assert stored.retry_count == 440
    assert "Quelle fehlt:" in stored.last_error

    migrated = queue.json_path.read_bytes()
    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        second = run_once(queue, force_pause=True)

    assert second["pending_start"] == 0
    assert provider.pause_calls == 0
    assert queue.json_path.read_bytes() == migrated


def test_missing_source_is_blocked_by_execution_fallback(tmp_path):
    """Die Ausführungsklassifikation schützt auch nach der Pause-Vorprüfung."""
    task = Task(chain=[Step(
        op="move",
        src=str(tmp_path / "missing.txt"),
        arg=str(tmp_path / "target.txt"),
    )])

    assert execute_chain(task) is False
    assert task.last_outcome == "blocked"
    assert "Quelle fehlt:" in task.last_error


def test_source_appearing_after_pause_preflight_is_moved(tmp_path, monkeypatch):
    """Eine zwischen Vorprüfung und Ausführung auftauchende Quelle wird genutzt."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    queue = Queue(tmp_path / "queue")
    queue.add(Task(
        chain=[Step(op="move", src=str(src), arg=str(dst))],
        retry_count=10,
    ))
    provider = FakeProvider()

    original_lstat = type(src).lstat

    def appearing_lstat(path):
        if path == src and not src.exists():
            src.write_text("appeared", encoding="utf-8")
            raise FileNotFoundError(str(path))
        return original_lstat(path)

    monkeypatch.setattr(type(src), "lstat", appearing_lstat)
    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        summary = run_once(queue, force_pause=True)

    assert summary["done"] == 1
    assert provider.pause_calls == 0
    assert dst.read_text(encoding="utf-8") == "appeared"


def test_idempotent_move_with_existing_target_does_not_pause(tmp_path):
    dst = tmp_path / "already-moved.txt"
    dst.write_text("present", encoding="utf-8")
    queue = Queue(tmp_path / "queue")
    queue.add(Task(
        chain=[Step(op="move", src=str(tmp_path / "missing.txt"), arg=str(dst))],
        retry_count=10,
    ))
    provider = FakeProvider()

    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        summary = run_once(queue, force_pause=True)

    assert summary["done"] == 1
    assert provider.pause_calls == 0
    assert queue.tasks[0].status == "done"


def test_missing_delete_source_is_noop_without_pause(tmp_path):
    queue = Queue(tmp_path / "queue")
    queue.add(Task(
        chain=[Step(op="delete", src=str(tmp_path / "already-gone.txt"))],
        retry_count=10,
    ))
    provider = FakeProvider()

    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        summary = run_once(queue, force_pause=True)

    assert summary["done"] == 1
    assert provider.pause_calls == 0
    assert queue.tasks[0].status == "done"


def test_successful_move_and_delete_are_unchanged(tmp_path):
    move_src = tmp_path / "move-source.txt"
    move_dst = tmp_path / "move-target.txt"
    delete_src = tmp_path / "delete-me.txt"
    move_src.write_text("move", encoding="utf-8")
    delete_src.write_text("delete", encoding="utf-8")
    queue = Queue(tmp_path / "queue")
    queue.add(Task(chain=[Step(op="move", src=str(move_src), arg=str(move_dst))]))
    queue.add(Task(chain=[Step(op="delete", src=str(delete_src))]))

    with patch("cloudlockfixer.worker.provider_for", return_value=None):
        summary = run_once(queue)

    assert summary["done"] == 2
    assert summary["blocked"] == 0
    assert move_dst.read_text(encoding="utf-8") == "move"
    assert not move_src.exists()
    assert not delete_src.exists()
