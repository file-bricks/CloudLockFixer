"""Hermetische Regressionstests: Bugsweep 2026-10-09 — CloudLockFixer.

Testet Resilienz in Provider-Erkennung, Einstellungen (interval_min & tmp-Cleanup),
Modell-Serialisierung (Task/Queue Fehlertoleranz), CWD-Validierung in Move-Operationen,
Verzeichnisstrukturen im Payload-Digest sowie Recovery unterbrochener Case-Renames.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import pytest

from cloudlockfixer import cli, ops, providers, settings
from cloudlockfixer.models import Queue, Task, parse_txt_line


def test_provider_for_and_owns_path_safety():
    """provider_for und owns_path müssen None, Leerstrings und CWD-Pfade sicher abweisen."""
    # 1. provider_for
    assert providers.provider_for(None) is None
    assert providers.provider_for("") is None
    assert providers.provider_for("   ") is None
    assert providers.provider_for(".") is None
    assert providers.provider_for("./") is None
    assert providers.provider_for(".\\") is None

    # 2. owns_path über alle registrierten Provider
    for prov in providers.available_providers():
        assert prov.owns_path(None) is False
        assert prov.owns_path("") is False
        assert prov.owns_path("   ") is False
        assert prov.owns_path(".") is False
        assert prov.owns_path("./") is False
        assert prov.owns_path(".\\") is False


def test_googledrive_provider_detection_and_resume_paths(monkeypatch, tmp_path: Path):
    """GoogleDriveProvider erkennt Standard-Home-Ordner und prüft moderne Pfade beim Resume."""
    gd = providers.GoogleDriveProvider()

    # Home-Ordner Erkennung
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    drive_dir = fake_home / "Google Drive"
    drive_dir.mkdir()

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    gd._cached_roots = None
    roots = gd._roots()
    assert drive_dir in roots

    # Resume-Pfade
    called_cmds = []

    def fake_popen(cmd):
        called_cmds.append(cmd)
        return None

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    fake_prog = tmp_path / "Program Files" / "Google" / "Drive"
    fake_prog.mkdir(parents=True)
    fake_exe = fake_prog / "GoogleDriveFS.exe"
    fake_exe.write_text("fake binary", encoding="utf-8")

    monkeypatch.setattr(gd, "_RESUME_BASE", tmp_path / "nonexistent")
    # Patch bases im sys.platform == "win32" Zweig via monkeypatching oder Direkttest
    if pytest.importorskip("sys").platform == "win32":
        # Erstelle Fake Pfad in bases
        orig_exists = Path.exists
        def mock_exists(p):
            if str(p) == r"C:\Program Files\Google\Drive":
                return True
            if str(p) == r"C:\Program Files\Google\Drive\GoogleDriveFS.exe":
                return True
            return orig_exists(p)

        monkeypatch.setattr(Path, "exists", mock_exists)
        res = gd.resume()
        assert res is True
        assert len(called_cmds) > 0


def test_settings_interval_min_validation_and_tmp_cleanup(tmp_path: Path, monkeypatch):
    """get_interval_min und set_interval_min validieren Werte; save räumt tmp-Dateien auf."""
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "_path", lambda: settings_file)

    cfg = {}
    # Default bei fehlendem oder ungültigem Wert
    assert settings.get_interval_min(cfg) == settings.DEFAULT_INTERVAL_MIN
    assert settings.get_interval_min({"interval_min": None}) == settings.DEFAULT_INTERVAL_MIN
    assert settings.get_interval_min({"interval_min": "invalid"}) == settings.DEFAULT_INTERVAL_MIN
    assert settings.get_interval_min({"interval_min": -10}) == settings.DEFAULT_INTERVAL_MIN
    assert settings.get_interval_min({"interval_min": 0}) == settings.DEFAULT_INTERVAL_MIN
    assert settings.get_interval_min({"interval_min": True}) == settings.DEFAULT_INTERVAL_MIN

    # Gültige Zuweisung
    settings.set_interval_min(cfg, 15)
    assert cfg["interval_min"] == 15
    assert settings.get_interval_min(cfg) == 15
    assert settings_file.exists()

    # Ungültige Werte werfen ValueError
    with pytest.raises(ValueError):
        settings.set_interval_min(cfg, 0)
    with pytest.raises(ValueError):
        settings.set_interval_min(cfg, -5)
    with pytest.raises(ValueError):
        settings.set_interval_min(cfg, "30")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        settings.set_interval_min(cfg, True)  # type: ignore[arg-type]

    # Test tmp cleanup bei Fehler
    tmp_file = settings_file.with_suffix(".json.tmp")
    def fail_replace(self, target):
        raise OSError("Permission denied simulated")

    monkeypatch.setattr(Path, "replace", fail_replace)
    settings.save({"interval_min": 20})
    assert not tmp_file.exists()


def test_task_from_dict_and_queue_load_resilience(tmp_path: Path):
    """Task.from_dict und Queue.load sind fehlertolerant bei None-Werten und beschädigten Task-Einträgen."""
    # 1. Task.from_dict mit chain=None
    t1 = Task.from_dict({"id": "t1", "chain": None})
    assert t1.chain == []

    # 2. Task.from_dict mit korrupten Elementen in chain
    t2 = Task.from_dict({
        "id": "t2",
        "chain": [None, "invalid_step", 42, {"op": "delete", "src": "file.txt"}]
    })
    assert len(t2.chain) == 1
    assert t2.chain[0].op == "delete"
    assert t2.chain[0].src == "file.txt"

    # 3. Queue.load mit einem korrupten Task und einem intakten Task
    queue_file = tmp_path / "queue.json"
    queue_data = {
        "tasks": [
            {"id": "bad", "chain": "not_a_list"},
            {"id": "corrupt_item", "chain": [{"op": "move"}]},  # Missing src/arg raises TypeError in Step
            {"id": "good", "chain": [{"op": "delete", "src": "valid.txt"}]}
        ]
    }
    queue_file.write_text(json.dumps(queue_data), encoding="utf-8")

    q = Queue(tmp_path)
    q.load()
    assert len(q.tasks) == 2
    task_ids = [t.id for t in q.tasks]
    assert "bad" in task_ids
    assert "good" in task_ids


def test_parse_txt_line_and_cli_move_rejects_dot(tmp_path: Path, monkeypatch, capsys):
    """parse_txt_line und CLI add --move weisen '.' / './' / '.\\' als Quelle oder Ziel ab."""
    # parse_txt_line
    with pytest.raises(ValueError, match="Arbeitsverzeichnis"):
        parse_txt_line('move "." "target"')

    with pytest.raises(ValueError, match="Arbeitsverzeichnis"):
        parse_txt_line('move "src" "."')

    with pytest.raises(ValueError, match="Arbeitsverzeichnis"):
        parse_txt_line('move "./" "target"')

    with pytest.raises(ValueError, match="Arbeitsverzeichnis"):
        parse_txt_line(r'move "src" ".\"')

    # CLI add --move
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    code1 = cli.main(["add", "--move", ".", "target"])
    assert code1 == 2
    assert "arbeitsverzeichnis" in capsys.readouterr().err.lower()

    code2 = cli.main(["add", "--move", "source", "."])
    assert code2 == 2
    assert "arbeitsverzeichnis" in capsys.readouterr().err.lower()


def test_payload_signature_includes_empty_directory_structure(tmp_path: Path):
    """_payload_signature unterscheidet Verzeichnisse mit leeren Unterordnern von Verzeichnissen ohne."""
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    # Beide haben dieselbe Datei
    (dir_a / "file.txt").write_text("common content", encoding="utf-8")
    (dir_b / "file.txt").write_text("common content", encoding="utf-8")

    sig_a1 = ops._payload_signature(dir_a)
    sig_b1 = ops._payload_signature(dir_b)
    assert sig_a1[2] == sig_b1[2]  # Gleiche Signatur

    # Leeren Unterordner in dir_b anlegen
    (dir_b / "empty_sub").mkdir()

    sig_b2 = ops._payload_signature(dir_b)
    # Die Signaturen müssen sich nun unterscheiden, da dir_b eine zusätzliche Verzeichnisstruktur hat
    assert sig_a1[2] != sig_b2[2]


def test_do_move_interrupted_case_rename_recovery(tmp_path: Path):
    """_do_move stellt einen unterbrochenen Case-Rename aus .clf_tmp_* wieder her."""
    f = tmp_path / "document.txt"
    f.write_text("case sensitive content", encoding="utf-8")
    dst = tmp_path / "DOCUMENT.TXT"

    # Simuliere Zustand nach Schritt 1 (src -> tmp), bevor Schritt 2 (tmp -> dst) stattfand
    tmp_suffix = hashlib.sha256(str(dst).encode("utf-8")).hexdigest()[:8]
    interrupted_tmp = f.with_name(f"{f.name}.clf_tmp_{tmp_suffix}")
    f.rename(interrupted_tmp)

    assert not f.exists()
    assert interrupted_tmp.exists()

    # Ausführen von _do_move(f, dst)
    ok, msg, noop = ops._do_move(f, dst)
    assert ok is True
    assert "wiederaufgenommen" in msg or "umbenannt" in msg
    assert dst.exists()
    assert not interrupted_tmp.exists()
