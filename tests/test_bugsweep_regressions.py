"""Regressionstests: Bugsweep Lauf #10 — CloudLockFixer."""
from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "cloudlockfixer"


# ---------------------------------------------------------------------------
# Bug #10-1: QSystemTrayIcon.Trigger statt QSystemTrayIcon.ActivationReason.Trigger
# ---------------------------------------------------------------------------

def test_tray_uses_activation_reason_enum():
    """_on_activated() muss ActivationReason.Trigger nutzen, nicht deprecated .Trigger (Bug #10-1)."""
    src = (SRC / "tray.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "_on_activated"):
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Compare):
                continue
            for comp in sub.comparators:
                if isinstance(comp, ast.Attribute) and comp.attr == "Trigger":
                    val = comp.value
                    if isinstance(val, ast.Attribute) and val.attr == "ActivationReason":
                        return  # korrekte Form gefunden
                    raise AssertionError(
                        "Bug #10-1: QSystemTrayIcon.Trigger verwendet — "
                        "muss QSystemTrayIcon.ActivationReason.Trigger sein (PySide6 6.4+)"
                    )
    # kein Compare mit .Trigger gefunden — ebenfalls OK (kein Vergleich)


# ---------------------------------------------------------------------------
# Bug #10-2: _ingest_txt() kein try/except OSError bei write_text/replace
# ---------------------------------------------------------------------------

def test_ingest_txt_survives_oserror(tmp_path):
    """_ingest_txt() darf bei OSError beim Schreiben nicht abstürzen (Bug #10-2)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from unittest.mock import patch
    from cloudlockfixer.models import Queue

    q = Queue(tmp_path)
    txt = tmp_path / "queue.txt"
    txt.write_text("delete /some/path\n", encoding="utf-8")

    with patch("pathlib.Path.write_text", side_effect=OSError("locked")):
        try:
            q.load()
        except OSError:
            raise AssertionError("_ingest_txt() muss OSError intern abfangen (Bug #10-2)")


# ---------------------------------------------------------------------------
# Bug #10-3: settings.save() kein try/except OSError
# ---------------------------------------------------------------------------

def test_settings_save_survives_oserror(tmp_path):
    """settings.save() darf bei OSError nicht abstürzen (Bug #10-3)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from unittest.mock import patch
    import cloudlockfixer.settings as s

    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        try:
            s.save({"interval_min": 60})
        except OSError:
            raise AssertionError("settings.save() muss OSError intern abfangen (Bug #10-3)")


# ---------------------------------------------------------------------------
# Bug #10-4: ops.py User-facing Strings mit ASCII-Digraphen
# ---------------------------------------------------------------------------

def test_ops_no_digraphs_in_return_strings():
    """ops.py return-Strings dürfen keine ASCII-Digraphe enthalten (Bug #10-4)."""
    import re
    src = (SRC / "ops.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    digraph_re = re.compile(
        r"\b(?:geloescht|uebersprungen|loeschen|unvollstaendig|spaeter|"
        r"fuer|rueckgabe|fuehrt|verzoegert|naechste)\b",
        re.IGNORECASE,
    )
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            m = digraph_re.search(node.value)
            if m:
                violations.append(f"Z.{node.lineno}: '{m.group()}'")
    assert not violations, (
        "ASCII-Digraphe in ops.py Strings (Bug #10-4) — echte Umlaute verwenden:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Bug #10-5: Autostart-Befehl zeigte im PyInstaller-Build auf clf_launcher.pyw
# ---------------------------------------------------------------------------

def test_autostart_uses_frozen_executable(monkeypatch):
    """Frozen Builds müssen sich selbst registrieren, nicht den Source-Launcher."""
    import sys
    import cloudlockfixer.autostart as autostart

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\_Local_DEV\CloudLockFixer\CloudLockFixer.exe")

    cmd = autostart._launch_command()

    assert cmd == r'"C:\_Local_DEV\CloudLockFixer\CloudLockFixer.exe"'
    assert "clf_launcher.pyw" not in cmd


# ---------------------------------------------------------------------------
# Bug #11-1: Case-Only Rename/Move fälschlich als 'bereits am Ziel' ignoriert
# ---------------------------------------------------------------------------

def test_case_only_rename_file(tmp_path):
    """Reine Groß-/Kleinschreibungsänderung einer Datei muss auf Datenträger angewendet werden."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.ops import rename_path

    f = tmp_path / "hello.txt"
    f.write_text("content", encoding="utf-8")
    ok, msg = rename_path(f, "HELLO.TXT")

    assert ok, msg
    assert (tmp_path / "HELLO.TXT").resolve().name == "HELLO.TXT"
    assert (tmp_path / "HELLO.TXT").read_text(encoding="utf-8") == "content"


def test_case_only_rename_directory(tmp_path):
    """Reine Groß-/Kleinschreibungsänderung eines Ordners muss auf Datenträger angewendet werden."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.ops import rename_path

    sub = tmp_path / "myFolder"
    sub.mkdir()
    (sub / "item.txt").write_text("nested_data", encoding="utf-8")

    ok, msg = rename_path(sub, "MYFOLDER")

    assert ok, msg
    assert (tmp_path / "MYFOLDER").resolve().name == "MYFOLDER"
    assert (tmp_path / "MYFOLDER" / "item.txt").read_text(encoding="utf-8") == "nested_data"


def test_case_only_move_file(tmp_path):
    """move_path mit reiner Case-Änderung muss auf Datenträger angewendet werden."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.ops import move_path

    f = tmp_path / "test_case.txt"
    f.write_text("data", encoding="utf-8")
    ok, msg = move_path(f, tmp_path / "TEST_CASE.TXT")

    assert ok, msg
    assert (tmp_path / "TEST_CASE.TXT").resolve().name == "TEST_CASE.TXT"


def test_case_only_rename_two_stage_fallback(tmp_path, monkeypatch):
    """Wenn direkter os.replace bei Case-Rename scheitert, greift der zweistufige Zwischenschritt."""
    import os
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    import cloudlockfixer.ops as ops

    f = tmp_path / "flaky.txt"
    f.write_text("flaky_data", encoding="utf-8")

    real_replace = os.replace
    calls = {"count": 0}

    def flaky_replace(src, dst):
        calls["count"] += 1
        # Ersten direkten In-Place-Versuch fehlschlagen lassen
        if calls["count"] == 1:
            raise PermissionError("Sharing violation (simuliert)")
        return real_replace(src, dst)

    monkeypatch.setattr(ops.os, "replace", flaky_replace)

    ok, msg = ops.rename_path(f, "FLAKY.TXT")
    assert ok, msg
    assert "Zwischenschritt" in msg
    assert (tmp_path / "FLAKY.TXT").resolve().name == "FLAKY.TXT"
    assert (tmp_path / "FLAKY.TXT").read_text(encoding="utf-8") == "flaky_data"


def test_rename_identical_case_reports_already_at_target(tmp_path):
    """Exakt identischer Name und Case meldet ohne Aktion 'bereits am Ziel'."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.ops import rename_path

    f = tmp_path / "same_case.txt"
    f.write_text("data", encoding="utf-8")

    ok, msg = rename_path(f, "same_case.txt")
    assert ok
    assert "bereits am Ziel" in msg


def test_worker_executes_case_only_rename_task(tmp_path):
    """Queue-Task mit Case-Only Rename wird vom Worker erfolgreich abgearbeitet."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.models import Queue, Step, Task
    from cloudlockfixer.worker import run_once

    f = tmp_path / "queue_file.txt"
    f.write_text("queue_content", encoding="utf-8")

    q = Queue(tmp_path / "data")
    t = Task(chain=[Step(op="rename", src=str(f), arg="QUEUE_FILE.TXT")])
    q.add(t)

    summary = run_once(q)
    assert summary["done"] == 1
    assert q.tasks[0].status == "done"
    assert (tmp_path / "QUEUE_FILE.TXT").resolve().name == "QUEUE_FILE.TXT"


# ---------------------------------------------------------------------------
# Bug #12-1: Unset APPDATA / LOCALAPPDATA creates relative CWD candidate paths,
# and non-existent sync roots are erroneously accepted without validation
# ---------------------------------------------------------------------------

def test_unset_appdata_does_not_probe_relative_cwd_configs(tmp_path, monkeypatch):
    """Unset APPDATA/LOCALAPPDATA must not probe relative CWD directories (Bug #12-1)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.providers import (
        DropboxProvider,
        NextcloudProvider,
        _read_synology_custom_roots,
    )

    fake_sync = tmp_path / "CwdSyncDir"
    fake_sync.mkdir()

    # Create CWD folders that would be scanned if relative paths were constructed
    cwd_db = tmp_path / "Dropbox"
    cwd_db.mkdir()
    (cwd_db / "info.json").write_text(
        '{"personal": {"path": "' + str(fake_sync).replace("\\", "\\\\") + '"}}',
        encoding="utf-8",
    )

    cwd_nc = tmp_path / "Nextcloud"
    cwd_nc.mkdir()
    (cwd_nc / "nextcloud.cfg").write_text(
        f"0\\Folders\\1\\localPath={fake_sync.as_posix()}\n",
        encoding="utf-8",
    )

    cwd_syno = tmp_path / "SynologyDrive" / "config"
    cwd_syno.mkdir(parents=True)
    (cwd_syno / "settings.conf").write_text(
        f'local_path="{fake_sync.as_posix()}"\n',
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    db_roots = DropboxProvider()._detect_roots()
    assert fake_sync not in db_roots, "DropboxProvider should not scan relative CWD info.json"

    nc_roots = NextcloudProvider()._detect_roots()
    assert fake_sync not in nc_roots, "NextcloudProvider should not scan relative CWD nextcloud.cfg"

    syno_roots = _read_synology_custom_roots()
    assert fake_sync not in syno_roots, "SynologyDrive should not scan relative CWD SynologyDrive"


def test_nonexistent_sync_roots_are_filtered(tmp_path, monkeypatch):
    """Sync roots from configs or environment must be absolute and actually exist (Bug #12-1)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.providers import (
        DropboxProvider,
        NextcloudProvider,
        OneDriveProvider,
    )

    appdata = tmp_path / "AppData" / "Roaming"
    appdata.mkdir(parents=True)
    monkeypatch.setenv("APPDATA", str(appdata))

    missing_nc = tmp_path / "NonexistentNextcloudSync"
    nc_cfg_dir = appdata / "Nextcloud"
    nc_cfg_dir.mkdir(parents=True)
    (nc_cfg_dir / "nextcloud.cfg").write_text(
        f"0\\Folders\\1\\localPath={missing_nc.as_posix()}\n",
        encoding="utf-8",
    )

    missing_db = tmp_path / "NonexistentDropboxSync"
    db_info_dir = appdata / "Dropbox"
    db_info_dir.mkdir(parents=True)
    (db_info_dir / "info.json").write_text(
        '{"personal": {"path": "' + str(missing_db).replace("\\", "\\\\") + '"}}',
        encoding="utf-8",
    )

    missing_od = tmp_path / "NonexistentOneDriveCommercial"
    monkeypatch.setenv("OneDriveCommercial", str(missing_od))

    nc_roots = NextcloudProvider()._detect_roots()
    assert missing_nc not in nc_roots, "NextcloudProvider must filter non-existent sync roots"

    db_roots = DropboxProvider()._detect_roots()
    assert missing_db not in db_roots, "DropboxProvider must filter non-existent sync roots"

    od_roots = OneDriveProvider()._detect_roots()
    assert missing_od not in od_roots, "OneDriveProvider must filter non-existent sync roots"


def test_windows_resume_exe_candidates_are_strictly_absolute(monkeypatch):
    """Executable candidates in resume() must be strictly absolute paths (Bug #12-1)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from cloudlockfixer.providers import OneDriveProvider

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)

    prov = OneDriveProvider()
    for exe in prov._exe_candidates:
        assert exe.is_absolute(), f"Candidate {exe} must be an absolute path, not relative to CWD"
