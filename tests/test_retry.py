"""Tests für Wiederaufnahme- und Retry-Funktionen (CLI, Queue, Tray)."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from cloudlockfixer import cli, tray
from cloudlockfixer.models import Queue, Step, Task


def test_queue_retry_task_resets_failed_task_and_preserves_progress(tmp_path: Path):
    q = Queue(tmp_path)
    t = Task(
        chain=[
            Step(op="move", src="src1.txt", arg="dst1.txt", copied=True),
            Step(op="delete", src="src2.txt"),
        ],
        id="task001",
        status="failed",
        retry_count=5,
        last_error="Cloud lock error WinError 32",
        last_outcome="permanent",
        step_index=1,
    )
    q.add(t)

    ret = q.retry_task("task001")
    assert ret is not None
    assert ret.id == "task001"
    assert ret.status == "pending"
    assert ret.retry_count == 0
    assert ret.last_outcome == "retryable"
    assert ret.step_index == 1
    assert ret.chain[0].copied is True
    assert ret.last_error == "Cloud lock error WinError 32"

    # Verifiziere Persistenz via Reload
    q2 = Queue(tmp_path)
    loaded = q2.tasks[0]
    assert loaded.status == "pending"
    assert loaded.retry_count == 0
    assert loaded.last_outcome == "retryable"
    assert loaded.step_index == 1
    assert loaded.chain[0].copied is True


def test_queue_retry_task_handles_blocked_task(tmp_path: Path):
    q = Queue(tmp_path)
    t = Task(
        chain=[Step(op="rename", src="src.txt", arg="dst.txt")],
        id="task002",
        status="blocked",
        retry_count=2,
        last_error="Target collision",
        last_outcome="blocked",
    )
    q.add(t)

    ret = q.retry_task("task002")
    assert ret is not None
    assert ret.status == "pending"
    assert ret.retry_count == 0
    assert ret.last_outcome == "retryable"


def test_queue_retry_task_unknown_id_returns_none(tmp_path: Path):
    q = Queue(tmp_path)
    t = Task(chain=[Step(op="delete", src="file.txt")], id="task003", status="failed")
    q.add(t)

    ret = q.retry_task("unknown_id")
    assert ret is None
    assert q.tasks[0].status == "failed"


def test_queue_retry_all_resets_only_failed_and_blocked(tmp_path: Path):
    q = Queue(tmp_path)
    t_failed = Task(chain=[Step(op="delete", src="1")], id="f1", status="failed", retry_count=3)
    t_blocked = Task(chain=[Step(op="delete", src="2")], id="b1", status="blocked", retry_count=1)
    t_done = Task(chain=[Step(op="delete", src="3")], id="d1", status="done", retry_count=1)
    t_pending = Task(chain=[Step(op="delete", src="4")], id="p1", status="pending", retry_count=2)

    q.add(t_failed)
    q.add(t_blocked)
    q.add(t_done)
    q.add(t_pending)

    retried = q.retry_all(failed_only=True)
    assert len(retried) == 2
    retried_ids = {tk.id for tk in retried}
    assert retried_ids == {"f1", "b1"}

    assert t_failed.status == "pending" and t_failed.retry_count == 0
    assert t_blocked.status == "pending" and t_blocked.retry_count == 0
    assert t_done.status == "done" and t_done.retry_count == 1
    assert t_pending.status == "pending" and t_pending.retry_count == 2


def test_queue_retry_all_returns_empty_when_no_failed(tmp_path: Path):
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="1")], id="d1", status="done"))
    q.add(Task(chain=[Step(op="delete", src="2")], id="p1", status="pending"))

    retried = q.retry_all()
    assert retried == []


def test_cli_retry_existing_task(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="bad.txt")], id="abc12345", status="failed"))

    code = cli.main(["retry", "abc12345"])
    assert code == 0
    captured = capsys.readouterr()
    assert "abc12345" in captured.out
    assert "delete 'bad.txt'" in captured.out

    q2 = Queue(tmp_path)
    assert q2.tasks[0].status == "pending"


def test_cli_retry_nonexistent_task(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="bad.txt")], id="abc12345", status="failed"))

    code = cli.main(["retry", "not_there"])
    assert code == 1
    captured = capsys.readouterr()
    assert "not_there" in captured.err


def test_cli_retry_all_with_failed_tasks(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="bad1.txt")], id="f1", status="failed"))
    q.add(Task(chain=[Step(op="delete", src="bad2.txt")], id="f2", status="blocked"))

    code = cli.main(["retry-all"])
    assert code == 0
    captured = capsys.readouterr()
    assert "2" in captured.out

    q2 = Queue(tmp_path)
    assert all(tk.status == "pending" for tk in q2.tasks)


def test_cli_retry_all_no_failed_tasks(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="good.txt")], id="d1", status="done"))

    code = cli.main(["retry-all"])
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out.strip()


def test_tray_retry_failed_action_and_status_refresh(tmp_path: Path, monkeypatch):
    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    monkeypatch.setattr(tray, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tray, "available_providers", lambda: [])

    # Erstelle Queue mit 1 failed Task
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src="fail.txt")], id="f1", status="failed"))

    tray_app = tray.TrayApp(app)
    assert hasattr(tray_app, "retry_failed_action")
    assert tray_app.retry_failed_action.isEnabled() is True
    assert "1" in tray_app.retry_failed_action.text()

    # Führe Retry-Action aus
    run_async_called = []
    monkeypatch.setattr(tray_app, "run_async", lambda force: run_async_called.append(force))

    tray_app._retry_failed_tasks()
    assert len(run_async_called) == 1
    assert run_async_called[0] is False

    # Nach dem Retry: keine failed Tasks mehr -> Action deaktiviert
    assert tray_app.retry_failed_action.isEnabled() is False
