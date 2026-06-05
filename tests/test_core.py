"""Tests fuer den plattformneutralen Kern: ops, models/Queue, worker (ohne Cloud)."""
import os
import stat
from pathlib import Path

import pytest

from cloudlockfixer import ops
from cloudlockfixer.models import Queue, Step, Task, parse_txt_line
from cloudlockfixer.worker import run_once


def _mkdir_with_file(p: Path, content="x"):
    p.mkdir(parents=True, exist_ok=True)
    (p / "f.txt").write_text(content, encoding="utf-8")
    return p


def test_delete_readonly_tree(tmp_path):
    """Regression (Lifetest 2026-05-29): read-only Verzeichnisse/Dateien (z.B.
    .pytest_cache, von OneDrive 'pinned') liessen rmtree mit WinError 5 scheitern.
    _delete_path muss das RO-Attribut saeubern und trotzdem loeschen."""
    root = tmp_path / "ro"
    nested = root / ".pytest_cache" / "v" / "cache"
    nested.mkdir(parents=True)
    f = nested / "nodeids"
    f.write_text("data", encoding="utf-8")
    # read-only auf Datei UND Verzeichnisse setzen (reproduziert den de-Windows-Fall)
    os.chmod(f, stat.S_IREAD)
    for d in (nested, nested.parent, nested.parent.parent, root):
        os.chmod(d, stat.S_IREAD)
    ok, msg = ops._delete_path(root)
    assert ok, msg
    assert not root.exists()


# ── ops: move/rename (in-place + copy+delete-Fallback) ──────────────

def test_rename_inplace(tmp_path):
    src = _mkdir_with_file(tmp_path / "old")
    ok, msg = ops.rename_path(src, "new")
    assert ok, msg
    assert (tmp_path / "new" / "f.txt").exists()
    assert not src.exists()


def test_move_to_other_dir(tmp_path):
    src = _mkdir_with_file(tmp_path / "a" / "x")
    dst = tmp_path / "b" / "x"
    ok, msg = ops.move_path(src, dst)
    assert ok, msg
    assert (dst / "f.txt").exists() and not src.exists()


def test_move_falls_back_to_copy_delete(tmp_path, monkeypatch):
    """os.replace scheitern lassen -> copy+delete-Pfad muss greifen."""
    src = _mkdir_with_file(tmp_path / "old", "payload")
    dst = tmp_path / "new"

    def boom(*a, **k):
        raise PermissionError("Zugriff verweigert (simuliert)")

    monkeypatch.setattr(ops.os, "replace", boom)
    ok, msg = ops.move_path(src, dst)
    assert ok, msg
    assert "copy+delete" in msg
    assert (dst / "f.txt").read_text(encoding="utf-8") == "payload"
    assert not src.exists()


def test_step_idempotent_after_copy_without_delete(tmp_path, monkeypatch):
    """Copy ok, aber Quelle gesperrt -> step.copied gemerkt; Retry loescht nur
    die Quelle (kein Re-Copy, kein Datenverlust)."""
    src = _mkdir_with_file(tmp_path / "old", "p")
    dst = tmp_path / "new"
    step = Step(op="move", src=str(src), arg=str(dst))
    monkeypatch.setattr(ops.os, "replace",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    real_delete = ops._delete_path
    calls = {"n": 0}

    def flaky_delete(p):
        calls["n"] += 1
        if calls["n"] == 1:
            return False, "gesperrt (simuliert)"
        return real_delete(p)

    monkeypatch.setattr(ops, "_delete_path", flaky_delete)
    ok1, _ = ops.execute_step(step)
    assert not ok1 and dst.exists() and src.exists() and step.copied  # halb-fertig
    ok2, msg2 = ops.execute_step(step)  # Retry: nur Quelle loeschen
    assert ok2, msg2
    assert dst.exists() and not src.exists()


def test_verify_fail_cleans_dst_allows_retry(tmp_path, monkeypatch):
    """Regression: wenn _verify_copy nach erfolgreicher Kopie fehlschlaegt,
    muss dst aufgeraeumt werden — sonst blockiert 'Ziel existiert' den Retry."""
    src = _mkdir_with_file(tmp_path / "old", "payload")
    dst = tmp_path / "new"
    monkeypatch.setattr(ops.os, "replace",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    monkeypatch.setattr(ops, "_verify_copy", lambda s, d: False)
    ok1, msg1 = ops.move_path(src, dst)
    assert not ok1 and "Verify" in msg1
    assert not dst.exists(), "dst muss bei Verify-Fehler aufgeraeumt sein"
    monkeypatch.undo()
    ok2, msg2 = ops.move_path(src, dst)
    assert ok2, f"Retry muss klappen: {msg2}"


def test_move_conflict_when_dst_differs(tmp_path):
    src = _mkdir_with_file(tmp_path / "old", "A")
    dst = _mkdir_with_file(tmp_path / "new", "B")  # anderer Inhalt
    ok, msg = ops.move_path(src, dst)
    assert not ok and "Konflikt" in msg
    assert src.exists() and dst.exists()  # nichts zerstoert


# ── Ketten: delete erst nach Erfolg ─────────────────────────────────

def test_chain_move_then_delete(tmp_path):
    """User-Usecase: geaenderten lokalen Ordner an Zielort + alten loeschen."""
    local_new = _mkdir_with_file(tmp_path / "local_new", "neu")
    target = tmp_path / "cloud" / "ProjektNeu"
    old = _mkdir_with_file(tmp_path / "cloud" / "ProjektAlt", "alt")
    task = Task(chain=[
        Step(op="move", src=str(local_new), arg=str(target)),
        Step(op="delete", src=str(old)),
    ])
    assert ops.execute_chain(task)
    assert task.status == "done"
    assert (target / "f.txt").read_text(encoding="utf-8") == "neu"
    assert not old.exists() and not local_new.exists()


def test_chain_stops_and_keeps_for_retry(tmp_path):
    """Schlaegt Schritt 1 fehl, darf Schritt 2 (delete) NICHT laufen."""
    missing = tmp_path / "gibtsnicht"
    victim = _mkdir_with_file(tmp_path / "victim")
    task = Task(chain=[
        Step(op="move", src=str(missing), arg=str(tmp_path / "ziel")),
        Step(op="delete", src=str(victim)),
    ])
    assert not ops.execute_chain(task)
    assert task.step_index == 0
    assert victim.exists()  # delete wurde NICHT ausgefuehrt


# ── txt-Parsing ─────────────────────────────────────────────────────

def test_parse_txt_variants():
    assert parse_txt_line("# comment") is None
    assert parse_txt_line("   ") is None
    t = parse_txt_line('rename "C:\\a b\\old" "neu"')
    assert t.chain[0].op == "rename" and t.chain[0].arg == "neu"
    t2 = parse_txt_line('move "x" "y" && delete "z"')
    assert [s.op for s in t2.chain] == ["move", "delete"]
    with pytest.raises(ValueError):
        parse_txt_line("frobnicate x")


# ── Queue: json + txt-Ingest + Roundtrip ────────────────────────────

def test_queue_txt_ingest_and_roundtrip(tmp_path):
    q = Queue(tmp_path)
    q.txt_path.write_text('rename "C:\\foo\\old" "new"\n', encoding="utf-8")
    q.load()  # liest txt -> Task
    assert len(q.tasks) == 1 and q.tasks[0].chain[0].op == "rename"
    # txt-Zeile wurde auskommentiert (kein Doppel-Ingest)
    q2 = Queue(tmp_path)
    assert len(q2.tasks) == 1
    # json-Roundtrip
    assert q2.tasks[0].id == q.tasks[0].id


def test_settings_load_returns_defaults_on_non_dict_json(tmp_path, monkeypatch):
    """settings.load() muss Default zurückgeben wenn JSON kein dict ist."""
    import cloudlockfixer.settings as smod
    monkeypatch.setattr(smod, "data_dir", lambda: tmp_path)
    for bad in ("null", "[]", "42", "{bad json"):
        (tmp_path / "settings.json").write_text(bad, encoding="utf-8")
        result = smod.load()
        assert isinstance(result, dict), f"Erwartet dict für bad JSON={bad!r}"
        assert "interval_min" in result


def test_settings_load_returns_defaults_on_invalid_utf8(tmp_path, monkeypatch):
    """Bug-Fix: settings.json mit ungueltigem UTF-8 (z.B. Disk-Korruption) ->
    Defaults, kein UnicodeDecodeError-Crash. json.JSONDecodeError faengt
    UnicodeDecodeError NICHT ab -- ValueError als gemeinsame Basisklasse noetig."""
    import cloudlockfixer.settings as smod
    monkeypatch.setattr(smod, "data_dir", lambda: tmp_path)
    (tmp_path / "settings.json").write_bytes(b"\xff\xfe{bad")
    result = smod.load()
    assert isinstance(result, dict), "settings.load() muss bei ungueltigem UTF-8 Defaults liefern"
    assert "interval_min" in result


def test_queue_load_returns_empty_on_invalid_utf8(tmp_path):
    """Bug-Fix: queue.json mit ungueltigem UTF-8 -> leere Tasks, kein UnicodeDecodeError.
    json.JSONDecodeError faengt UnicodeDecodeError NICHT ab -- ValueError noetig."""
    q = Queue(tmp_path)
    q.json_path.write_bytes(b"\xff\xfe{bad")
    q.load()
    assert q.tasks == [], "Queue.load() muss bei ungueltigem UTF-8 leere Tasks liefern"


def test_settings_save_atomic_no_tmp_leftover(tmp_path, monkeypatch):
    """settings.save() muss atomar schreiben (tmp ersetzen) — kein .json.tmp Überrest."""
    import cloudlockfixer.settings as smod
    monkeypatch.setattr(smod, "data_dir", lambda: tmp_path)
    smod.save({"interval_min": 60, "language": "de"})
    p = tmp_path / "settings.json"
    assert p.exists(), "settings.json muss nach save() existieren"
    assert not (tmp_path / "settings.json.tmp").exists(), "Kein .tmp-Überrest erlaubt"
    loaded = smod.load()
    assert loaded["interval_min"] == 60 and loaded["language"] == "de"


def test_ingest_txt_atomic_write(tmp_path):
    """Regression (Bug 6): _ingest_txt muss queue.txt atomar schreiben
    (tmp-Datei + replace). Kein .txt.tmp-Überrest nach Ingest."""
    q = Queue(tmp_path)
    q.txt_path.write_text('delete "C:\\\\foo\\\\bar"\n', encoding="utf-8")
    q.load()
    assert len(q.tasks) == 1
    assert not (tmp_path / "queue.txt.tmp").exists(), ".txt.tmp-Datei darf nach Ingest nicht übrig bleiben"


def test_queue_load_returns_empty_on_corrupt_json(tmp_path):
    """Queue.load darf nicht abstürzen wenn queue.json kein dict-Root enthält."""
    q = Queue(tmp_path)
    for bad in ("", "{bad json", "null", "[]", "42"):
        q.json_path.write_text(bad, encoding="utf-8")
        q.load()
        assert q.tasks == [], f"Erwartet leere Liste für bad JSON={bad!r}"


def test_task_from_dict_tolerates_unknown_step_fields(tmp_path):
    """Bug-Fix (Bug 10): Step(**s) ohne Feldfilterung -> TypeError bei unbekannten
    Feldern -> alle Tasks still verloren. from_dict muss unbekannte Step-Felder
    ignorieren (Forward-Compat, manuelle Queue-Edits)."""
    import json
    q = Queue(tmp_path)
    payload = {
        "version": 1,
        "saved_at": "2026-01-01T00:00:00+00:00",
        "tasks": [{
            "id": "aabbcc00",
            "status": "pending",
            "retry_count": 0,
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_try": "",
            "last_error": "",
            "step_index": 0,
            "chain": [{
                "op": "delete",
                "src": "/tmp/x",
                "arg": "",
                "copied": False,
                "zukunftsfeld": "x",   # unbekanntes Feld
            }],
        }],
    }
    q.json_path.write_text(json.dumps(payload), encoding="utf-8")
    q.load()
    assert len(q.tasks) == 1, (
        "Task muss geladen werden — unbekannte Step-Felder duerfen nicht zu "
        "TypeError -> silent task-loss fuehren"
    )
    assert q.tasks[0].chain[0].op == "delete"


# ── worker ohne Cloud (provider_for -> None) ────────────────────────

def test_queue_txt_ingest_handles_invalid_utf8(tmp_path):
    """Bug-Fix (Bug 12): queue.txt mit ungueltigem UTF-8 muss Queue.load() ueberleben.
    UnicodeDecodeError war ungefangen -> Queue-Init scheiterte komplett.
    Erwartet: tasks bleibt leer, kein Exception."""
    q = Queue(tmp_path)
    q.txt_path.write_bytes(b"\xff\xfe rename corrupted\n")
    q.load()
    assert q.tasks == [], (
        "_ingest_txt darf bei ungueltigem UTF-8 in queue.txt nicht werfen -- "
        "tasks muss leer bleiben"
    )


def test_worker_runs_local_task(tmp_path):
    q = Queue(tmp_path)
    src = _mkdir_with_file(tmp_path / "old")
    q.add(Task(chain=[Step(op="rename", src=str(src), arg="new")]))
    summary = run_once(q, force_pause=False)
    assert summary["done"] == 1
    assert (tmp_path / "new").exists()


# ── CLI ─────────────────────────────────────────────────────────────

def test_cli_chain_invalid_op_returns_2(tmp_path, monkeypatch):
    """Regression (Bug 8): 'clf add --chain' mit ungueltigem Op darf KEINEN
    Traceback (ValueError) erzeugen — muss Return-Code 2 + Fehlermeldung liefern."""
    import cloudlockfixer.cli as cli_mod
    import cloudlockfixer.paths as paths_mod
    monkeypatch.setattr(paths_mod, "data_dir", lambda: tmp_path)
    rc = cli_mod.main(["add", "--chain", "frobnicate x"])
    assert rc == 2
