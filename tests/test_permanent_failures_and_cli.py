"""Tests für Resume-Garantie, on_permanent_failure Hook, failed.txt und CLI-Befehle (cancel, list --failed).

Alle Tests arbeiten ausschließlich mit Fake-Providern und Mocks; es werden niemals
reale Prozesse gestartet oder beendet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cloudlockfixer import cli
from cloudlockfixer.models import Queue, Step, Task
from cloudlockfixer.worker import run_once


class FakeProvider:
    name = "FakeDrive"
    mount_type = "folder"

    def __init__(self, pause_result: bool = True, resume_result: bool = True, raise_on_pause: bool = False, raise_on_resume: bool = False) -> None:
        self.pause_calls = 0
        self.resume_calls = 0
        self.pause_result = pause_result
        self.resume_result = resume_result
        self.raise_on_pause = raise_on_pause
        self.raise_on_resume = raise_on_resume

    def is_running(self) -> bool:
        return True

    def pause(self) -> bool:
        self.pause_calls += 1
        if self.raise_on_pause:
            raise RuntimeError("FakeProvider pause failure")
        return self.pause_result

    def resume(self) -> bool:
        self.resume_calls += 1
        if self.raise_on_resume:
            raise RuntimeError("FakeProvider resume failure")
        return self.resume_result


# ── Resume-Garantie (o1-Befund) ──────────────────────────────────────


def test_resume_guarantee_called_even_if_pause_returned_false(tmp_path: Path):
    """Resume-Garantie: Wenn der Client vorab lief, muss resume() auch dann aufgerufen
    werden, wenn pause() False zurueckgab (z.B. 1,5-s-Timeout bei langsamem Kill)."""
    data_dir = tmp_path / "queue"
    queue = Queue(data_dir)
    src = tmp_path / "locked.txt"
    src.write_text("content", encoding="utf-8")
    dst = tmp_path / "dst.txt"
    task = Task(chain=[Step(op="move", src=str(src), arg=str(dst))], retry_count=5)
    queue.add(task)

    provider = FakeProvider(pause_result=False)

    with patch("cloudlockfixer.worker.provider_for", return_value=provider):
        summary = run_once(queue, force_pause=True)

    assert provider.pause_calls == 1
    assert provider.resume_calls == 1, "Resume muss trotz pause() == False aufgerufen werden"
    assert summary["paused_providers"] == []


def test_resume_guarantee_when_second_provider_raises(tmp_path: Path):
    """Wenn die Pause-Schleife beim 2. Provider abbricht, muss der 1. Provider
    trotzdem im finally wieder aufgenommen werden."""
    data_dir = tmp_path / "queue"
    queue = Queue(data_dir)
    src = tmp_path / "file.txt"
    src.write_text("hello", encoding="utf-8")
    queue.add(Task(chain=[Step(op="delete", src=str(src))], retry_count=5))

    prov1 = FakeProvider(pause_result=True)
    prov1.name = "Prov1"
    prov2 = FakeProvider(raise_on_pause=True)
    prov2.name = "Prov2"

    with patch("cloudlockfixer.worker._providers_to_pause", return_value={prov1, prov2}):
        run_once(queue, force_pause=True)

    assert prov1.pause_calls == 1
    assert prov1.resume_calls == 1, "Prov1 muss im finally resumet werden"
    assert prov2.pause_calls == 1
    assert prov2.resume_calls == 1, "Prov2 muss ebenfalls im finally versucht werden"


def test_resume_failure_and_exception_do_not_crash_worker(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    """Fehlgeschlagene resume()-Aufrufe werden geloggt und unterbrechen den Worker nicht."""
    data_dir = tmp_path / "queue"
    queue = Queue(data_dir)
    src = tmp_path / "file.txt"
    src.write_text("ok", encoding="utf-8")
    dst = tmp_path / "dst.txt"
    queue.add(Task(chain=[Step(op="move", src=str(src), arg=str(dst))], retry_count=5))

    prov1 = FakeProvider(resume_result=False)
    prov1.name = "FailingResumeProv"
    prov2 = FakeProvider(raise_on_resume=True)
    prov2.name = "ExceptingResumeProv"

    with patch("cloudlockfixer.worker._providers_to_pause", return_value={prov1, prov2}):
        summary = run_once(queue, force_pause=True)

    assert summary["done"] == 1
    assert prov1.resume_calls == 1
    assert prov2.resume_calls == 1


# ── on_permanent_failure Hook, failed.txt & Idempotenz ──────────────


def test_permanent_failure_writes_failed_txt_and_triggers_hook(tmp_path: Path):
    """Dauerhaft scheiternde Tasks schreiben nach failed.txt und fuehren den Hook aus."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    queue = Queue(data_dir)
    src = tmp_path / "missing_source.txt"
    dst = tmp_path / "dest.txt"
    task = Task(chain=[Step(op="move", src=str(src), arg=str(dst))])
    queue.add(task)

    marker_file = tmp_path / "hook_executed.json"
    record_script = tmp_path / "record.py"
    record_script.write_text(
        "import sys, json\n"
        "data = {'id': sys.argv[1], 'op': sys.argv[2], 'src': sys.argv[3], 'dst': sys.argv[4]}\n"
        f"with open(r'{marker_file}', 'w', encoding='utf-8') as f:\n"
        "    json.dump(data, f)\n",
        encoding="utf-8",
    )
    hook_template = f'"{sys.executable}" "{record_script}" "{{task_id}}" "{{op}}" "{{src}}" "{{dst}}"'

    summary = run_once(queue, on_permanent_failure=hook_template)

    assert summary["blocked"] == 1
    failed_txt = data_dir / "failed.txt"
    assert failed_txt.is_file(), "failed.txt muss angelegt werden"
    content = failed_txt.read_text(encoding="utf-8")
    assert f"task_id={task.id}" in content
    assert "status=blocked" in content
    assert "op=move" in content
    assert "Quelle fehlt:" in content

    assert marker_file.is_file(), "on_permanent_failure Hook muss ausgefuehrt worden sein"
    data = json.loads(marker_file.read_text(encoding="utf-8"))
    assert data["id"] == task.id
    assert data["op"] == "move"
    assert data["src"] == str(src)
    assert data["dst"] == str(dst)

    # Idempotenz-Pruefung: Weiterer Durchlauf darf Hook/failed.txt nicht erneut aufrufen
    marker_file.unlink()
    initial_txt_len = len(content.splitlines())

    summary2 = run_once(queue, on_permanent_failure=hook_template)
    assert summary2["pending_start"] == 0
    assert not marker_file.exists(), "Hook darf bei zweitem Lauf nicht erneut triggern (Idempotenz)"
    new_txt_len = len(failed_txt.read_text(encoding="utf-8").splitlines())
    assert new_txt_len == initial_txt_len, "failed.txt darf keine Duplikate enthalten"


def test_max_retries_reached_writes_failed_txt_and_marks_failure_reported(tmp_path: Path):
    """Erreicht ein Task max_retries, wird er failed/permanent und reported."""
    data_dir = tmp_path / "data"
    queue = Queue(data_dir)
    src = tmp_path / "locked.txt"
    src.write_text("data", encoding="utf-8")
    dst = tmp_path / "out.txt"
    task = Task(chain=[Step(op="move", src=str(src), arg=str(dst))], retry_count=4)
    queue.add(task)

    with patch("cloudlockfixer.worker.execute_chain", return_value=False):
        summary = run_once(queue, max_retries=5)

    assert summary["failed_permanent"] == 1
    assert queue.tasks[0].status == "failed"
    assert queue.tasks[0].last_outcome == "permanent"
    assert queue.tasks[0].failure_reported is True

    failed_txt = data_dir / "failed.txt"
    assert failed_txt.exists()
    assert f"task_id={task.id}" in failed_txt.read_text(encoding="utf-8")


def test_retry_resets_failure_reported_flag(tmp_path: Path):
    """Wird ein Task manuell mit retry zurueckgesetzt, wird failure_reported zurueckgesetzt."""
    queue = Queue(tmp_path)
    task = Task(
        chain=[Step(op="delete", src="file.txt")],
        status="failed",
        retry_count=5,
        last_outcome="permanent",
        failure_reported=True,
    )
    queue.add(task)

    ret = queue.retry_task(task.id)
    assert ret is not None
    assert ret.status == "pending"
    assert ret.failure_reported is False


# ── CLI: clf cancel <task-id> ────────────────────────────────────────


def test_cli_cancel_pending_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    task = Task(chain=[Step(op="delete", src="test.txt")], id="abc12345", status="pending")
    queue.add(task)

    exit_code = cli.main(["cancel", "abc12345"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "abc12345" in out

    reloaded = Queue(tmp_path)
    saved = reloaded.get_task("abc12345")
    assert saved is not None
    assert saved.status == "failed"
    assert saved.last_outcome == "permanent"
    assert saved.failure_reported is True
    assert "Abgebrochen" in saved.last_error or "Canceled" in saved.last_error

    # Idempotenz bei erneutem Cancel eines bereits 'failed' Tasks (Befund 4):
    first_last_error = saved.last_error
    exit_code_again = cli.main(["cancel", "abc12345"])
    assert exit_code_again == 0
    reloaded2 = Queue(tmp_path)
    saved2 = reloaded2.get_task("abc12345")
    assert saved2.status == "failed"
    assert saved2.last_error == first_last_error


def test_cli_cancel_blocked_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    task = Task(chain=[Step(op="move", src="a", arg="b")], id="blk00001", status="blocked", last_error="Quelle fehlt: a")
    queue.add(task)

    assert cli.main(["cancel", "blk00001"]) == 0
    saved = Queue(tmp_path).get_task("blk00001")
    assert saved.status == "failed"
    assert saved.last_outcome == "permanent"
    assert "Quelle fehlt: a" in saved.last_error


def test_cli_cancel_already_done_task_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    task = Task(chain=[Step(op="delete", src="test.txt")], id="done0001", status="done")
    queue.add(task)

    assert cli.main(["cancel", "done0001"]) == 1
    err = capsys.readouterr().err
    assert "done0001" in err


def test_cli_cancel_unknown_task_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    Queue(tmp_path)

    assert cli.main(["cancel", "unknown9"]) == 1
    err = capsys.readouterr().err
    assert "unknown9" in err


# ── CLI: clf list --failed und --status ──────────────────────────────


def test_cli_list_failed_filters_correctly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    queue.add(Task(chain=[Step(op="delete", src="1")], id="t_pend", status="pending"))
    queue.add(Task(chain=[Step(op="delete", src="2")], id="t_fail", status="failed"))
    queue.add(Task(chain=[Step(op="delete", src="3")], id="t_done", status="done"))
    queue.add(Task(chain=[Step(op="delete", src="4")], id="t_blck", status="blocked"))

    assert cli.main(["list", "--failed"]) == 0
    out = capsys.readouterr().out
    assert "t_fail" in out
    assert "t_blck" in out
    assert "t_pend" not in out
    assert "t_done" not in out


def test_cli_list_failed_when_none_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    queue.add(Task(chain=[Step(op="delete", src="1")], id="t_pend", status="pending"))

    assert cli.main(["list", "--failed"]) == 0
    out = capsys.readouterr().out
    assert "t_pend" not in out
    assert "Keine fehlgeschlagenen" in out or "No failed" in out


def test_cli_list_status_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    queue = Queue(tmp_path)
    queue.add(Task(chain=[Step(op="delete", src="1")], id="t_pend", status="pending"))
    queue.add(Task(chain=[Step(op="delete", src="2")], id="t_fail", status="failed"))

    assert cli.main(["list", "--status", "pending"]) == 0
    out = capsys.readouterr().out
    assert "t_pend" in out
    assert "t_fail" not in out

    # Status-Filter ohne Treffer liefert differenzierte Rueckmeldung statt "Queue leer" (Befund 3)
    assert cli.main(["list", "--status", "done"]) == 0
    out_empty = capsys.readouterr().out
    assert "done" in out_empty
    assert "Queue leer" not in out_empty


def test_on_permanent_failure_hook_injection_safety(tmp_path: Path):
    """Regressionstest gegen Command- und Argument-Injection im on_permanent_failure Hook.

    Verifiziert, dass shell=False gesetzt ist, Platzhalter mit Shell-Metazeichen
    (&, ;, ", Leerzeichen) sicher als diskrete Argumente und Umgebungsvariablen
    uebergeben werden und keine Shell-Ausfuehrung stattfindet.
    """
    from cloudlockfixer.worker import _record_permanent_failure

    data_dir = tmp_path / "data"
    evil_src = tmp_path / 'foo & calc.exe ; "bar".txt'
    evil_dst = tmp_path / 'dest & echo evil.txt'
    evil_err = 'Access denied & format c: ; "quoted error"'
    task = Task(
        chain=[Step(op="move", src=str(evil_src), arg=str(evil_dst))],
        last_error=evil_err,
        status="failed",
        last_outcome="permanent",
    )

    hook_template = 'myhook --src "{src}" --dst "{dst}" --error "{error}" --task-id {task_id} --op {op}'

    with patch("cloudlockfixer.worker.subprocess.run") as mock_run:
        _record_permanent_failure(task, data_dir, hook_template)

    assert mock_run.call_count == 1
    call_args, call_kwargs = mock_run.call_args

    assert call_kwargs.get("shell") is False, "shell=False muss explizit gesetzt sein"
    assert call_kwargs.get("check") is False
    assert call_kwargs.get("timeout") == 30

    expected_args = [
        "myhook",
        "--src",
        str(evil_src),
        "--dst",
        str(evil_dst),
        "--error",
        evil_err,
        "--task-id",
        task.id,
        "--op",
        "move",
    ]
    assert call_args[0] == expected_args

    env = call_kwargs.get("env")
    assert env is not None
    assert env.get("CLF_TASK_ID") == task.id
    assert env.get("CLF_OP") == "move"
    assert env.get("CLF_SRC") == str(evil_src)
    assert env.get("CLF_DST") == str(evil_dst)
    assert env.get("CLF_ERROR") == evil_err
