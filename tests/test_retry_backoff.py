"""Tests für gedeckeltes exponentielles Backoff und konfigurierbares Retry-Verhalten (Task 172)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cloudlockfixer import cli, settings, worker
from cloudlockfixer.models import Queue, Step, Task


def test_task_is_due_defaults_and_timestamps():
    now = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
    t = Task(chain=[Step(op="delete", src="file.txt")])

    # 1. Ohne next_try_at sofort fällig
    assert t.is_due(now) is True

    # 2. In der Vergangenheit liegender Zeitstempel fällig
    past = (now - timedelta(seconds=10)).isoformat()
    t.next_try_at = past
    assert t.is_due(now) is True

    # 3. Exakt jetziger Zeitstempel fällig
    t.next_try_at = now.isoformat()
    assert t.is_due(now) is True

    # 4. In der Zukunft liegender Zeitstempel nicht fällig
    future = (now + timedelta(seconds=30)).isoformat()
    t.next_try_at = future
    assert t.is_due(now) is False

    # 5. Korrupter/ungültiger Zeitstempel als Fallback sofort fällig
    t.next_try_at = "ungueltiges-datum"
    assert t.is_due(now) is True


def test_task_compute_next_retry_exponential_and_cap():
    now = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
    t = Task(chain=[Step(op="delete", src="file.txt")])

    # Versuch 1: base_sec * 2^0 = 60s
    t.retry_count = 1
    next_time_iso = t.compute_next_retry(base_sec=60, max_sec=3600, now_dt=now)
    expected_1 = now + timedelta(seconds=60)
    assert datetime.fromisoformat(next_time_iso) == expected_1

    # Versuch 2: base_sec * 2^1 = 120s
    t.retry_count = 2
    next_time_iso = t.compute_next_retry(base_sec=60, max_sec=3600, now_dt=now)
    expected_2 = now + timedelta(seconds=120)
    assert datetime.fromisoformat(next_time_iso) == expected_2

    # Versuch 4: base_sec * 2^3 = 480s
    t.retry_count = 4
    next_time_iso = t.compute_next_retry(base_sec=60, max_sec=3600, now_dt=now)
    expected_4 = now + timedelta(seconds=480)
    assert datetime.fromisoformat(next_time_iso) == expected_4

    # Hoher Retry-Zähler: gedeckelt bei max_sec (3600s)
    t.retry_count = 15
    next_time_iso = t.compute_next_retry(base_sec=60, max_sec=3600, now_dt=now)
    expected_cap = now + timedelta(seconds=3600)
    assert datetime.fromisoformat(next_time_iso) == expected_cap


def test_queue_retry_clears_next_try_at(tmp_path: Path):
    q = Queue(tmp_path)
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    t = Task(
        chain=[Step(op="delete", src="file.txt")],
        id="task_b1",
        status="failed",
        retry_count=5,
        next_try_at=future,
    )
    q.add(t)

    # 1. Einzel-Retry
    ret = q.retry_task("task_b1")
    assert ret is not None
    assert ret.status == "pending"
    assert ret.retry_count == 0
    assert ret.next_try_at == ""

    # Reload verifiziert Persistenz
    q2 = Queue(tmp_path)
    assert q2.tasks[0].next_try_at == ""

    # 2. retry_all
    q2.tasks[0].status = "blocked"
    q2.tasks[0].next_try_at = future
    q2.save()

    retried = q2.retry_all()
    assert len(retried) == 1
    assert retried[0].next_try_at == ""


def test_settings_backoff_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()

    # Defaults
    assert settings.get_backoff_base(cfg) == 60
    assert settings.get_backoff_max(cfg) == 3600

    # Custom Werte setzen und persistieren
    settings.set_backoff_base(cfg, 30)
    settings.set_backoff_max(cfg, 1800)

    loaded = settings.load()
    assert settings.get_backoff_base(loaded) == 30
    assert settings.get_backoff_max(loaded) == 1800

    # Validierung
    with pytest.raises(ValueError):
        settings.set_backoff_base(loaded, 0)
    with pytest.raises(ValueError):
        settings.set_backoff_base(loaded, -10)
    with pytest.raises(ValueError):
        settings.set_backoff_base(loaded, "invalid")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        settings.set_backoff_max(loaded, 0)
    with pytest.raises(ValueError):
        settings.set_backoff_max(loaded, "invalid")  # type: ignore[arg-type]


def test_worker_run_once_backoff_scheduling_and_deferral(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    q = Queue(tmp_path)
    t = Task(chain=[Step(op="delete", src="locked.txt")], id="t_lock")
    q.add(t)

    # Mock execute_chain to fail retryably
    def mock_fail(task):
        task.last_error = "WinError 32 File locked"
        task.last_outcome = "retryable"
        return False

    monkeypatch.setattr(worker, "execute_chain", mock_fail)

    # 1. Erster Lauf: Task schlägt fehl, retry_count wird 1, next_try_at wird gesetzt
    summary1 = worker.run_once(q, backoff_base_sec=30, backoff_max_sec=300)
    task1 = q.tasks[0]
    assert summary1["done"] == 0
    assert summary1["failed_again"] == 1
    assert summary1["deferred"] == 0
    assert task1.retry_count == 1
    assert task1.status == "pending"
    assert task1.next_try_at != ""

    first_next = datetime.fromisoformat(task1.next_try_at)
    assert first_next > datetime.now(timezone.utc)

    # 2. Zweiter Lauf mit apply_backoff=True: Task ist noch nicht fällig -> wird deferred
    summary2 = worker.run_once(q, apply_backoff=True)
    task2 = q.tasks[0]
    assert summary2["done"] == 0
    assert summary2["failed_again"] == 0
    assert summary2["deferred"] == 1
    assert task2.retry_count == 1  # Zähler nicht erhöht

    # 3. Dritter Lauf mit apply_backoff=False (oder ignore_backoff=True): Task wird sofort ausgeführt
    summary3 = worker.run_once(q, apply_backoff=False, backoff_base_sec=30, backoff_max_sec=300)
    task3 = q.tasks[0]
    assert summary3["failed_again"] == 1
    assert summary3["deferred"] == 0
    assert task3.retry_count == 2
    second_next = datetime.fromisoformat(task3.next_try_at)
    assert second_next > first_next

    # 4. Erfolgreicher Lauf bereinigt next_try_at
    monkeypatch.setattr(worker, "execute_chain", lambda task: True)
    summary4 = worker.run_once(q, apply_backoff=False)
    task4 = q.tasks[0]
    assert summary4["done"] == 1
    assert task4.next_try_at == ""


def test_cli_list_and_run_now_ignore_backoff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)

    q = Queue(tmp_path)
    future = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    t = Task(
        chain=[Step(op="delete", src="file.txt")],
        id="t_cli",
        status="pending",
        retry_count=2,
        next_try_at=future,
    )
    q.add(t)

    # 1. clf list zeigt nächsten Versuch an
    code_list = cli.main(["list"])
    assert code_list == 0
    captured_list = capsys.readouterr()
    assert "t_cli" in captured_list.out
    assert "nächster Versuch:" in captured_list.out

    # 2. clf run-now --ignore-backoff ruft run_once mit ignore_backoff=True auf
    captured_kwargs = {}

    def mock_run_once(queue, force_pause=False, max_retries=None, ignore_backoff=False, **kwargs):
        captured_kwargs["ignore_backoff"] = ignore_backoff
        return {
            "done": 1,
            "failed_again": 0,
            "failed_permanent": 0,
            "blocked": 0,
            "deferred": 0,
            "pending_start": 1,
            "paused_providers": [],
        }

    monkeypatch.setattr(cli, "run_once", mock_run_once)

    code_run = cli.main(["run-now", "--ignore-backoff"])
    assert code_run == 0
    assert captured_kwargs["ignore_backoff"] is True


def test_providers_to_pause_skips_deferred_tasks():
    t_deferred = Task(
        chain=[Step(op="delete", src="C:/test/file1.txt")],
        next_try_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        retry_count=5,
    )
    t_due = Task(
        chain=[Step(op="delete", src="C:/test/file2.txt")],
        retry_count=5,
    )

    fake_prov = MagicMock()
    fake_prov.is_running.return_value = True
    fake_prov.mount_type = "folder"
    fake_prov.name = "FakeProvider"

    # With ignore_backoff=False: only due tasks
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(worker, "_task_paths", lambda tk: [Path(tk.chain[0].src)])
        mp.setattr(worker, "provider_for", lambda p: fake_prov)

        # Deferred alone does not trigger pause
        provs_deferred = worker._providers_to_pause([t_deferred], force_pause=False, ignore_backoff=False)
        assert len(provs_deferred) == 0

        # Due task causes pause even when deferred task is present
        provs_mixed = worker._providers_to_pause([t_deferred, t_due], force_pause=False, ignore_backoff=False)
        assert len(provs_mixed) == 1

        provs_forced = worker._providers_to_pause([t_deferred], force_pause=True, ignore_backoff=True)
        assert len(provs_forced) == 1
