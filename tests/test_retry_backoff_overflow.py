"""Persisted high retry counters must not abort an unlimited retry queue."""
from datetime import datetime, timedelta, timezone

import pytest

from cloudlockfixer import worker
from cloudlockfixer.models import Queue, Step, Task


@pytest.mark.parametrize("retry_count", [1024, 1025, 100_000, 10**100])
def test_large_retry_count_stays_at_cap(retry_count):
    now = datetime(2026, 9, 30, tzinfo=timezone.utc)
    task = Task(chain=[Step(op="delete", src="locked.txt")], retry_count=retry_count)
    assert datetime.fromisoformat(task.compute_next_retry(now_dt=now)) == now + timedelta(hours=1)


@pytest.mark.parametrize("retry_count,base,cap,expected", [
    (1, 1, 7, 1), (2, 1, 7, 2), (3, 1, 7, 4), (4, 1, 7, 7),
    (6, 60, 3600, 1920), (7, 60, 3600, 3600), (10**100, 10, 8, 8),
])
def test_exponential_growth_and_custom_caps(retry_count, base, cap, expected):
    now = datetime(2026, 9, 30, tzinfo=timezone.utc)
    task = Task(chain=[], retry_count=retry_count)
    assert datetime.fromisoformat(task.compute_next_retry(base, cap, now)) == now + timedelta(seconds=expected)


def test_worker_persists_retry_and_processes_later_tasks_after_high_counter(tmp_path, monkeypatch):
    queue = Queue(tmp_path)
    queue.add(Task(chain=[Step(op="delete", src="locked.txt")], id="locked", retry_count=1024))
    queue.add(Task(chain=[Step(op="delete", src="other.txt")], id="other"))
    monkeypatch.setattr(worker, "_providers_to_pause", lambda *args, **kwargs: set())

    def execute(task):
        if task.id == "locked":
            task.last_error = "WinError 32 File locked"
            task.last_outcome = "retryable"
            return False
        task.status = "done"
        return True

    monkeypatch.setattr(worker, "execute_chain", execute)
    summary = worker.run_once(queue, apply_backoff=True)
    assert summary["failed_again"] == 1
    assert summary["done"] == 1
    reloaded = Queue(tmp_path)
    reloaded.load()
    locked, other = reloaded.tasks
    assert locked.status == "pending" and locked.retry_count == 1025
    assert locked.next_try_at and locked.last_error == "WinError 32 File locked"
    assert other.status == "done"
