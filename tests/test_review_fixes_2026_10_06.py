"""Regressionstests: Code-Review 2026-10-06 — CloudLockFixer.

Deckt ab: Symlink-Löschung ohne Fehl-Erfolg, Link-sicherer Lock-Fallback,
Queue-Merge bei parallelen Prozessen, run-now-Backoff-Semantik, dokumentierte
Backoff-Flags, konfigurierbarer Multiplikator und lauffähige Nautilus-Skripte.
"""
from __future__ import annotations

import errno
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

import pytest

from cloudlockfixer import cli, contextmenu, ops, paths, settings, worker
from cloudlockfixer.models import Queue, Step, Task

needs_symlinks = pytest.mark.skipif(
    sys.platform == "win32", reason="Symlinks brauchen unter Windows Zusatzrechte"
)


# ── ops: Symlinks / Links ──────────────────────────────────────────


@needs_symlinks
def test_delete_symlink_to_dir_removes_link_only(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep.txt").write_text("data", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)

    ok, msg = ops._delete_path(link)

    assert ok, msg
    assert not link.is_symlink(), "Link muss tatsächlich entfernt sein (kein Fehl-Erfolg)"
    assert (target / "keep.txt").read_text(encoding="utf-8") == "data"


@needs_symlinks
def test_delete_dangling_symlink(tmp_path: Path):
    link = tmp_path / "dangling"
    link.symlink_to(tmp_path / "missing")

    ok, msg = ops._delete_path(link)

    assert ok, msg
    assert not link.is_symlink()


@needs_symlinks
def test_skip_locked_fallback_never_enters_linked_dirs(tmp_path: Path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep", encoding="utf-8")

    tree = tmp_path / "tree"
    (tree / "sub").mkdir(parents=True)
    (tree / "sub" / "locked.txt").write_text("x", encoding="utf-8")
    (tree / "plain.txt").write_text("x", encoding="utf-8")
    (tree / "sub" / "link").symlink_to(outside, target_is_directory=True)

    original_unlink = Path.unlink

    def fake_unlink(self, missing_ok=False):
        if self.name == "locked.txt":
            raise OSError(errno.EBUSY, "EBUSY")
        return original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    ok, locked = ops._delete_dir_skip_locked(tree)

    assert not ok
    assert [p.name for p in locked] == ["locked.txt"]
    assert not (tree / "plain.txt").exists()
    assert not (tree / "sub" / "link").is_symlink()
    assert (outside / "precious.txt").read_text(encoding="utf-8") == "keep"


# ── Queue: parallele Prozesse ──────────────────────────────────────


def test_save_keeps_task_added_by_other_process(tmp_path: Path):
    tray_queue = Queue(tmp_path)
    tray_queue.add(Task(chain=[Step(op="delete", src=str(tmp_path / "a"))], id="tray0001"))

    # Ein zweiter Prozess (CLI) hängt während des Worker-Laufs einen Task an.
    cli_queue = Queue(tmp_path)
    cli_queue.add(Task(chain=[Step(op="delete", src=str(tmp_path / "b"))], id="cli00001"))

    tray_queue.tasks[0].retry_count = 3
    tray_queue.save()

    reloaded = Queue(tmp_path)
    by_id = {t.id: t for t in reloaded.tasks}
    assert set(by_id) == {"tray0001", "cli00001"}
    assert by_id["tray0001"].retry_count == 3


def test_run_once_does_not_drop_concurrently_added_task(tmp_path: Path, monkeypatch):
    q = Queue(tmp_path)
    q.add(Task(chain=[Step(op="delete", src=str(tmp_path / "gone"))], id="first001"))

    def execute_and_add(task: Task) -> bool:
        Queue(tmp_path).add(Task(chain=[Step(op="delete", src="x")], id="late0001"))
        task.status = "done"
        task.last_outcome = "done"
        return True

    monkeypatch.setattr(worker, "execute_chain", execute_and_add)
    monkeypatch.setattr(worker, "_providers_to_pause", lambda *a, **k: set())

    worker.run_once(q)

    ids = {t.id for t in Queue(tmp_path).tasks}
    assert ids == {"first001", "late0001"}


# ── run-now: Backoff-Semantik und Flags ────────────────────────────


def _future_task(tmp_path: Path) -> Queue:
    q = Queue(tmp_path)
    q.add(Task(
        chain=[Step(op="delete", src=str(tmp_path / "missing"))],
        id="defer001",
        retry_count=1,
        next_try_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    ))
    return q


@pytest.fixture
def cli_env(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(cli, "_setup_logging", lambda: None)
    monkeypatch.setattr(worker, "_providers_to_pause", lambda *a, **k: set())
    return tmp_path


def test_run_now_without_flag_runs_deferred_tasks_immediately(cli_env: Path):
    _future_task(cli_env)

    assert cli.main(["run-now"]) == 0

    task = Queue(cli_env).get_task("defer001")
    assert task.retry_count == 2, "Manueller Lauf darf ohne --backoff nicht aufschieben"
    assert task.status == "done"


def test_run_now_with_backoff_flag_defers(cli_env: Path):
    _future_task(cli_env)

    assert cli.main(["run-now", "--backoff"]) == 0

    task = Queue(cli_env).get_task("defer001")
    assert task.retry_count == 1


def test_run_now_passes_documented_backoff_flags(cli_env: Path, monkeypatch):
    captured: dict = {}

    def fake_run_once(queue, **kwargs):
        captured.update(kwargs)
        return {"done": 0, "failed_again": 0, "failed_permanent": 0, "blocked": 0,
                "deferred": 0, "pending_start": 0, "paused_providers": []}

    monkeypatch.setattr(cli, "run_once", fake_run_once)

    assert cli.main(["run-now", "--initial-delay", "5.0",
                     "--backoff-multiplier", "3", "--max-delay", "300"]) == 0
    assert captured["backoff_base_sec"] == 5.0
    assert captured["backoff_multiplier"] == 3.0
    assert captured["backoff_max_sec"] == 300.0
    assert captured["ignore_backoff"] is True


@pytest.mark.parametrize("argv", [
    ["run-now", "--initial-delay", "0"],
    ["run-now", "--max-delay", "-1"],
    ["run-now", "--max-delay", "nan"],
    ["run-now", "--backoff-multiplier", "0.5"],
    ["run-now", "--max-retries", "0"],
])
def test_run_now_rejects_invalid_backoff_values(cli_env: Path, argv):
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2


def test_run_now_does_not_rerun_worker_on_type_error(cli_env: Path, monkeypatch):
    calls = []

    def broken_run_once(queue, **kwargs):
        calls.append(kwargs)
        raise TypeError("bug inside worker")

    monkeypatch.setattr(cli, "run_once", broken_run_once)

    with pytest.raises(TypeError):
        cli.main(["run-now"])
    assert len(calls) == 1, "Ein TypeError darf keinen zweiten Worker-Lauf auslösen"


def test_compute_next_retry_uses_multiplier_and_cap():
    now = datetime(2026, 10, 6, tzinfo=timezone.utc)
    task = Task(chain=[Step(op="delete", src="x")], retry_count=3)

    at = task.compute_next_retry(10, 1000, now, multiplier=3.0)
    assert datetime.fromisoformat(at) == now + timedelta(seconds=90)

    task.retry_count = 10
    at = task.compute_next_retry(10, 1000, now, multiplier=3.0)
    assert datetime.fromisoformat(at) == now + timedelta(seconds=1000)


def test_compute_next_retry_constant_factor_is_bounded_for_huge_counters():
    now = datetime(2026, 10, 6, tzinfo=timezone.utc)
    task = Task(chain=[Step(op="delete", src="x")], retry_count=10**12)

    at = task.compute_next_retry(30, 600, now, multiplier=1.0)

    assert datetime.fromisoformat(at) == now + timedelta(seconds=30)


def test_backoff_multiplier_setting_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()
    assert settings.get_backoff_multiplier(cfg) == 2.0

    settings.set_backoff_multiplier(cfg, 1.5)
    assert settings.get_backoff_multiplier(settings.load()) == 1.5

    for bad in (0.5, 0, True, "2", 1000):
        with pytest.raises(ValueError):
            settings.set_backoff_multiplier(cfg, bad)
        assert settings.get_backoff_multiplier({"backoff_multiplier": bad}) == 2.0


# ── Kontextmenü: Nautilus-Skript ist tatsächlich lauffähig ──────────


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-Shellskript")
def test_nautilus_script_invokes_launcher_with_spaces_in_path(tmp_path: Path, monkeypatch):
    launcher_dir = tmp_path / "Cloud Lock"
    launcher_dir.mkdir()
    record = tmp_path / "argv.txt"
    fake_python = launcher_dir / "fake python"
    fake_python.write_text(
        "#!/bin/sh\n"
        f"for a in \"$@\"; do printf '%s\\n' \"$a\"; done >> '{record}'\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(paths, "pythonw", lambda: str(fake_python))
    monkeypatch.setattr(paths, "launcher",
                        lambda: PurePosixPath(str(launcher_dir / "clf_launcher.pyw")))

    assert contextmenu.install()
    script = tmp_path / "xdg" / "nautilus" / "scripts" / "CloudLockFixer" / "02_delayed_move.sh"
    env = {k: v for k, v in os.environ.items() if k != "NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"}
    result = subprocess.run([str(script), "/data/a b.txt"], capture_output=True,
                            text=True, env=env, timeout=30)

    assert result.returncode == 0, result.stderr
    assert record.read_text(encoding="utf-8").splitlines() == [
        str(launcher_dir / "clf_launcher.pyw"),
        "gui-add", "--op", "move", "--src", "/data/a b.txt",
    ]
