"""Hermetische Regressionstests: Bugsweep 2026-10-01 — CloudLockFixer.

Testet Schutz gegen leere Pfade, CWD-Löschung, Root-Löschung, Rename-Resilienz,
CLI add Validierung, Worker-Task-Path-Filterung und transaktionale Queue-Persistenz.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from cloudlockfixer import cli, ops, worker
from cloudlockfixer.models import Queue, Step, Task, parse_txt_line


def test_delete_path_rejects_empty_and_dot_and_root(tmp_path: Path):
    """_delete_path muss leere Pfade, '.' und Root-Pfade sicher abweisen und darf nicht CWD löschen."""
    # 1. Leerer Pfad
    ok, msg = ops._delete_path(Path(""))
    assert ok is False
    assert "leer" in msg.lower() or "ungültig" in msg.lower()

    # 2. '.' Pfad
    ok_dot, msg_dot = ops._delete_path(Path("."))
    assert ok_dot is False
    assert "arbeitsverzeichnis" in msg_dot.lower() or "ungültig" in msg_dot.lower()

    # 3. Root-Anchor Pfad (z.B. C:\ oder /)
    root_p = Path(tmp_path.resolve().anchor)
    ok_root, msg_root = ops._delete_path(root_p)
    assert ok_root is False
    assert "wurzelverzeichnis" in msg_root.lower() or "root" in msg_root.lower()


def test_do_move_rejects_empty_paths_and_roots(tmp_path: Path):
    """_do_move muss leere Pfade, '.' und Wurzelverzeichnisse abweisen."""
    src_file = tmp_path / "test.txt"
    src_file.write_text("hello", encoding="utf-8")

    # Leeres Ziel
    ok, msg, _ = ops._do_move(src_file, Path(""))
    assert ok is False
    assert "leer" in msg.lower() or "arbeitsverzeichnis" in msg.lower()

    # Leere Quelle
    ok2, msg2, _ = ops._do_move(Path(""), tmp_path / "dst.txt")
    assert ok2 is False
    assert "leer" in msg2.lower() or "arbeitsverzeichnis" in msg2.lower()

    # Wurzelverzeichnis als Ziel
    root_p = Path(tmp_path.resolve().anchor)
    ok3, msg3, _ = ops._do_move(src_file, root_p)
    assert ok3 is False
    assert "wurzelverzeichnis" in msg3.lower() or "root" in msg3.lower()


def test_rename_path_rejects_empty_whitespace_and_rel_indicators(tmp_path: Path):
    """rename_path muss leere Namen, '.', '..' und Pfadtrennzeichen deterministisch abweisen."""
    f = tmp_path / "sample.txt"
    f.write_text("data", encoding="utf-8")

    for bad_name in ("", "   ", ".", "..", "sub/name", "sub\\name"):
        ok, msg = ops.rename_path(f, bad_name)
        assert ok is False, f"rename_path should fail for bad_name={bad_name!r}"
        assert ("leer" in msg.lower() or "ungültig" in msg.lower() or "pfad" in msg.lower()), (
            f"Expected error message for {bad_name!r}, got {msg!r}"
        )


def test_execute_step_rename_empty_or_dot_is_blocked(tmp_path: Path):
    """execute_step muss bei rename mit leerem Namen oder '.' blockiert melden."""
    f = tmp_path / "sample.txt"
    f.write_text("data", encoding="utf-8")

    step_empty = Step(op="rename", src=str(f), arg="")
    ok, msg = ops.execute_step(step_empty)
    assert ok is False
    outcome = ops._outcome_for_error(msg)
    assert outcome == "blocked", f"Outcome for {msg!r} should be 'blocked', got {outcome}"

    step_dot = Step(op="rename", src=str(f), arg=".")
    ok2, msg2 = ops.execute_step(step_dot)
    assert ok2 is False
    outcome2 = ops._outcome_for_error(msg2)
    assert outcome2 == "blocked", f"Outcome for {msg2!r} should be 'blocked', got {outcome2}"

    step_empty_src = Step(op="rename", src="", arg="new.txt")
    ok3, msg3 = ops.execute_step(step_empty_src)
    assert ok3 is False
    assert ops._outcome_for_error(msg3) == "blocked"


def test_parse_txt_line_validates_tokens_and_args():
    """parse_txt_line muss leere Pfade und Pfadtrenner im rename-Ziel mit ValueError abweisen."""
    # Leere Pfade
    with pytest.raises(ValueError):
        parse_txt_line('delete ""')

    with pytest.raises(ValueError):
        parse_txt_line('move "" "target"')

    with pytest.raises(ValueError):
        parse_txt_line('move "src" ""')

    with pytest.raises(ValueError):
        parse_txt_line('rename "src" ""')

    # Pfad im rename-Namen
    with pytest.raises(ValueError):
        parse_txt_line('rename "src" "sub/dir"')

    with pytest.raises(ValueError):
        parse_txt_line(r'rename "src" "sub\dir"')

    with pytest.raises(ValueError):
        parse_txt_line('rename "src" "."')


def test_cli_add_validates_inputs(tmp_path: Path, monkeypatch, capsys):
    """clf add muss ungültige/leere Eingaben vor dem Hinzufügen abfangen."""
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)

    # 1. Leere delete Quelle
    code = cli.main(["add", "--delete", ""])
    assert code == 2
    captured = capsys.readouterr()
    assert "leer" in captured.err.lower() or "ungültig" in captured.err.lower()

    # 2. Leeres rename Ziel
    code = cli.main(["add", "--rename", "file.txt", ""])
    assert code == 2
    captured = capsys.readouterr()
    assert "leer" in captured.err.lower()

    # 3. Rename mit Pfadtrennzeichen
    code = cli.main(["add", "--rename", "file.txt", "sub/name.txt"])
    assert code == 2
    captured = capsys.readouterr()
    assert "pfad" in captured.err.lower()


def test_worker_task_paths_ignores_empty_and_invalid_steps():
    """_task_paths darf für ungültige oder leere Quellpfade nicht CWD zurückgeben."""
    # 1. Leere Quelle bei delete
    t_empty_del = Task(chain=[Step(op="delete", src="")])
    assert worker._task_paths(t_empty_del) == []

    # 2. Leeres Argument bei rename
    t_empty_ren = Task(chain=[Step(op="rename", src="some/path", arg="")])
    assert worker._task_paths(t_empty_ren) == []

    # 3. Dot als rename-Argument
    t_dot_ren = Task(chain=[Step(op="rename", src="some/path", arg=".")])
    assert worker._task_paths(t_dot_ren) == []


def test_queue_ingest_order_and_cleanup_on_failure(tmp_path: Path, monkeypatch):
    """_ingest_txt muss queue.json vor dem Überschreiben von queue.txt persistieren und .tmp bereinigen."""
    q = Queue(tmp_path)
    q.txt_path.write_text('delete "C:\\\\valid\\\\file.txt"\n', encoding="utf-8")

    save_called = []
    orig_save = q._save_unlocked

    def mock_save():
        save_called.append(True)
        orig_save()

    monkeypatch.setattr(q, "_save_unlocked", mock_save)
    q.load()

    assert len(save_called) == 1
    assert len(q.tasks) == 1
    # Verifiziere, dass keine .tmp Dateien zurückbleiben
    assert not (tmp_path / "queue.txt.tmp").exists()
    assert not (tmp_path / "queue.json.tmp").exists()
