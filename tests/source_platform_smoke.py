"""Source-Platform Smoke-Test für CloudLockFixer.

Prüft auf Linux und macOS (und Windows) ohne Cloud-Sync-Client oder GUI:
- Modul-Import und Version
- ops: rename, move, delete (plattformneutral, stdlib-only)
- models: parse_txt_line, Queue-Persistenz
- paths: data_dir cross-platform
- worker: run_once ohne Cloud-Provider
"""
from __future__ import annotations

from pathlib import Path


def test_version_defined():
    import cloudlockfixer
    assert cloudlockfixer.__version__
    assert "." in cloudlockfixer.__version__


def test_ops_delete_file(tmp_path):
    from cloudlockfixer.ops import _delete_path
    f = tmp_path / "target.txt"
    f.write_text("x", encoding="utf-8")
    ok, msg = _delete_path(f)
    assert ok, msg
    assert not f.exists()


def test_ops_rename_directory(tmp_path):
    from cloudlockfixer.ops import rename_path
    src = tmp_path / "old_dir"
    src.mkdir()
    (src / "file.txt").write_text("content", encoding="utf-8")
    ok, msg = rename_path(src, "new_dir")
    assert ok, msg
    assert (tmp_path / "new_dir" / "file.txt").exists()
    assert not src.exists()


def test_ops_move_path(tmp_path):
    from cloudlockfixer.ops import move_path
    src = tmp_path / "a" / "item"
    src.mkdir(parents=True)
    (src / "data.txt").write_text("payload", encoding="utf-8")
    dst = tmp_path / "b" / "item"
    ok, msg = move_path(src, dst)
    assert ok, msg
    assert (dst / "data.txt").read_text(encoding="utf-8") == "payload"
    assert not src.exists()


def test_parse_txt_line_variants():
    from cloudlockfixer.models import parse_txt_line
    assert parse_txt_line("# Kommentar") is None
    assert parse_txt_line("   ") is None
    t = parse_txt_line('delete "/tmp/testfile"')
    assert t is not None
    assert t.chain[0].op == "delete"
    assert t.chain[0].src == "/tmp/testfile"
    t2 = parse_txt_line('rename "/tmp/old" "new_name"')
    assert t2.chain[0].op == "rename"
    assert t2.chain[0].arg == "new_name"


def test_queue_add_and_roundtrip(tmp_path):
    from cloudlockfixer.models import Queue, Step, Task
    q = Queue(tmp_path)
    task = Task(chain=[Step(op="delete", src="/tmp/smoke_test_x")])
    q.add(task)
    q2 = Queue(tmp_path)
    assert len(q2.tasks) == 1
    assert q2.tasks[0].chain[0].op == "delete"
    assert q2.tasks[0].id == task.id


def test_paths_data_dir_cross_platform():
    from cloudlockfixer import paths
    d = paths.data_dir()
    assert isinstance(d, Path)
    # Linux/macOS: LOCALAPPDATA fehlt -> ~/.cloudlockfixer
    # Windows: %LOCALAPPDATA%\CloudLockFixer
    assert d.exists()


def test_worker_run_once_local(tmp_path):
    from cloudlockfixer.models import Queue, Step, Task
    from cloudlockfixer.worker import run_once
    q = Queue(tmp_path)
    src = tmp_path / "source.txt"
    src.write_text("smoke", encoding="utf-8")
    q.add(Task(chain=[Step(op="rename", src=str(src), arg="renamed.txt")]))
    summary = run_once(q, force_pause=False)
    assert summary["done"] == 1
    assert (tmp_path / "renamed.txt").exists()
    assert not src.exists()
