"""
Tests für EBUSY/Lock-Fehler-Erkennung und robuste Verzeichnis-Löschung.
Adressiert die 3 Bugs aus TODO.md (entdeckt via MCP-Integration 2026-05-31):

Bug 1: EBUSY als Retry-Trigger-Code
Bug 2: "Kopiert, Löschung ausstehend" — Status bei erfolgtem Copy + gesperrter Quelle
Bug 3: Verzeichnis-Rename mit gesperrter Innendatei
"""

import errno
import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cloudlockfixer import ops
from cloudlockfixer.ops import _is_lock_error, _LOCK_ERRNOS, _delete_dir_skip_locked
from cloudlockfixer.models import Queue, Step, Task


# ── Bug 1: _is_lock_error() erkennt EBUSY und verwandte Codes ──────────

class TestIsLockError:
    """_is_lock_error() identifiziert temporäre Lock-Fehler korrekt."""

    def _make_oserror(self, errno_code: int, winerror: int = 0) -> OSError:
        e = OSError(errno_code, os.strerror(errno_code))
        e.errno = errno_code
        if winerror:
            e.winerror = winerror
        return e

    def test_ebusy_is_lock_error(self):
        e = self._make_oserror(errno.EBUSY)
        assert _is_lock_error(e), "EBUSY muss als Lock-Fehler erkannt werden"

    def test_eperm_is_lock_error(self):
        e = self._make_oserror(errno.EPERM)
        assert _is_lock_error(e)

    def test_eacces_is_lock_error(self):
        e = self._make_oserror(errno.EACCES)
        assert _is_lock_error(e)

    def test_exdev_is_lock_error(self):
        e = self._make_oserror(errno.EXDEV)
        assert _is_lock_error(e), "EXDEV (cross-device) muss als Lock-Fehler gelten"

    def test_enoent_is_not_lock_error(self):
        e = self._make_oserror(errno.ENOENT)
        assert not _is_lock_error(e), "ENOENT ist ein permanenter Fehler, kein Lock"

    def test_eexist_is_not_lock_error(self):
        e = self._make_oserror(errno.EEXIST)
        assert not _is_lock_error(e)

    def test_windows_sharing_violation_winerror_32(self):
        e = OSError()
        e.errno = None
        e.winerror = 32  # ERROR_SHARING_VIOLATION
        assert _is_lock_error(e), "WinError 32 ist Sharing-Verletzung (= Lock)"

    def test_windows_lock_violation_winerror_33(self):
        e = OSError()
        e.errno = None
        e.winerror = 33  # ERROR_LOCK_VIOLATION
        assert _is_lock_error(e)

    def test_no_winerror_no_errno_is_not_lock_error(self):
        e = OSError("irgendein Fehler")
        e.errno = None
        assert not _is_lock_error(e)

    def test_lock_errnos_set_contains_ebusy(self):
        assert errno.EBUSY in _LOCK_ERRNOS

    def test_lock_errnos_set_contains_all_four_codes(self):
        expected = {errno.EBUSY, errno.EPERM, errno.EACCES, errno.EXDEV}
        assert expected <= _LOCK_ERRNOS, \
            f"_LOCK_ERRNOS muss mindestens {expected} enthalten"


# ── Bug 2: "Kopiert, Löschung ausstehend" — Status beim Retry ──────────

class TestCopiedPendingDelete:
    """Wenn Copy erfolgreich war aber Quelle noch gesperrt ist, bleibt Step retry-fähig."""

    def test_copied_flag_set_on_partial_move(self, tmp_path, monkeypatch):
        """Nach erfolgreichem Copy (Quelle noch gesperrt) muss step.copied=True sein."""
        src = tmp_path / "src.txt"
        src.write_text("payload", encoding="utf-8")
        dst = tmp_path / "dst.txt"

        # os.replace muss scheitern damit copy+delete-Pfad genommen wird
        eacces = OSError(errno.EACCES, "Access denied (cloud lock)")
        eacces.errno = errno.EACCES
        monkeypatch.setattr(ops.os, "replace", lambda *a, **k: (_ for _ in ()).throw(eacces))

        # Löschen der Quelle schlägt fehl (EBUSY)
        original_delete = ops._delete_path

        def fake_delete(p: Path):
            if p == src:
                e = OSError(errno.EBUSY, "Datei gesperrt")
                e.errno = errno.EBUSY
                return False, f"Loeschen fehlgeschlagen: {e}"
            return original_delete(p)

        monkeypatch.setattr(ops, "_delete_path", fake_delete)

        step = Step(op="move", src=str(src), arg=str(dst))
        ok, msg = ops.execute_step(step)

        assert not ok, "Schritt muss als fehlgeschlagen markiert sein (Quelle noch vorhanden)"
        assert step.copied, "step.copied muss True sein nach erfolgreichem Copy"
        assert dst.exists(), "Ziel muss vorhanden sein (Copy war erfolgreich)"

    def test_retry_after_copied_only_deletes_source(self, tmp_path):
        """Wenn step.copied=True und Ziel existiert, wird nur noch Quelle gelöscht."""
        src = tmp_path / "src.txt"
        src.write_text("data", encoding="utf-8")
        dst = tmp_path / "dst.txt"
        dst.write_text("data", encoding="utf-8")  # Ziel existiert bereits (vom Copy)

        step = Step(op="move", src=str(src), arg=str(dst), copied=True)
        ok, msg = ops.execute_step(step)

        assert ok, f"Retry-Schritt mit copied=True muss erfolgreich sein: {msg}"
        assert not src.exists(), "Quelle muss nach Retry gelöscht sein"
        assert dst.exists(), "Ziel darf beim Retry nicht angefasst werden"

    def test_error_message_mentions_locked_source(self, tmp_path, monkeypatch):
        """Fehlermeldung bei copy+lock soll auf Retry hinweisen."""
        src = tmp_path / "src.txt"
        src.write_text("x", encoding="utf-8")
        dst = tmp_path / "dst.txt"

        # os.replace scheitern lassen damit copy+delete genommen wird
        eacces = OSError(errno.EACCES, "Access denied")
        eacces.errno = errno.EACCES
        monkeypatch.setattr(ops.os, "replace", lambda *a, **k: (_ for _ in ()).throw(eacces))

        original_delete = ops._delete_path

        def fake_delete(p: Path):
            if p == src:
                e = OSError(errno.EBUSY, "busy")
                e.errno = errno.EBUSY
                return False, f"Loeschen fehlgeschlagen: {e}"
            return original_delete(p)

        monkeypatch.setattr(ops, "_delete_path", fake_delete)

        step = Step(op="move", src=str(src), arg=str(dst))
        ok, msg = ops.execute_step(step)

        assert not ok
        assert "gesperrt" in msg.lower() or "retry" in msg.lower() or "kopiert" in msg.lower(), \
            f"Meldung soll auf Lock/Retry hinweisen, war: '{msg}'"


# ── Bug 3: Verzeichnis mit gesperrter Innendatei ───────────────────────

class TestDeleteDirSkipLocked:
    """_delete_dir_skip_locked() bereinigt alles außer gesperrten Dateien."""

    def test_empty_dir_fully_deleted(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        ok, locked = _delete_dir_skip_locked(d)
        assert ok
        assert not d.exists()
        assert locked == []

    def test_normal_dir_fully_deleted(self, tmp_path):
        d = tmp_path / "normal"
        d.mkdir()
        (d / "a.txt").write_text("a", encoding="utf-8")
        (d / "sub").mkdir()
        (d / "sub" / "b.txt").write_text("b", encoding="utf-8")
        ok, locked = _delete_dir_skip_locked(d)
        assert ok
        assert not d.exists()

    def test_locked_file_reported_not_deleted(self, tmp_path, monkeypatch):
        """Datei die EBUSY wirft wird als 'gesperrt' gemeldet und übersprungen."""
        d = tmp_path / "withlock"
        d.mkdir()
        locked_file = d / "locked.txt"
        locked_file.write_text("locked", encoding="utf-8")
        (d / "normal.txt").write_text("ok", encoding="utf-8")

        original_unlink = Path.unlink

        def fake_unlink(self, missing_ok=False):
            if self.name == "locked.txt":
                e = OSError(errno.EBUSY, "EBUSY")
                e.errno = errno.EBUSY
                raise e
            return original_unlink(self, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", fake_unlink)

        ok, locked = _delete_dir_skip_locked(d)

        assert not ok, "Nicht vollständig gelöscht wenn Dateien gesperrt"
        assert len(locked) == 1
        assert locked[0].name == "locked.txt"

    def test_nonexistent_dir_returns_ok(self, tmp_path):
        d = tmp_path / "nichtda"
        ok, locked = _delete_dir_skip_locked(d)
        assert ok
        assert locked == []

    def test_delete_path_uses_skip_locked_on_ebusy_dir(self, tmp_path, monkeypatch):
        """_delete_path ruft _delete_dir_skip_locked auf wenn rmtree mit EBUSY scheitert."""
        d = tmp_path / "busydir"
        d.mkdir()
        (d / "f.txt").write_text("x", encoding="utf-8")

        # rmtree wirft EBUSY
        def fake_rmtree(p, **kwargs):
            e = OSError(errno.EBUSY, "EBUSY")
            e.errno = errno.EBUSY
            raise e

        skip_called = []

        def fake_skip(p):
            skip_called.append(p)
            return True, []

        monkeypatch.setattr(ops, "_rmtree", fake_rmtree)
        monkeypatch.setattr(ops, "_delete_dir_skip_locked", fake_skip)

        ok, msg = ops._delete_path(d)

        assert ok, f"_delete_path soll OK zurückgeben wenn skip_locked erfolgreich: {msg}"
        assert skip_called, "_delete_dir_skip_locked muss aufgerufen worden sein"


# ── Bug 4: leeres Verzeichnis mit gesperrtem EIGEN-Handle (z.B. Search-Indexer) ──

class TestEmptyDirOwnHandleLocked:
    """Regression: ein LEERES Verzeichnis, dessen eigenes Handle gesperrt ist
    (kein gesperrtes Kind, sondern der Ordner selbst — z.B. von SearchIndexer.exe
    gehalten), darf NICHT fälschlich als gelöscht ('completed') gemeldet werden.
    Sonst verwirft der Worker den Task statt ihn erneut zu versuchen (false-completed).
    """

    def _lock_rmdir(self, monkeypatch, target: Path) -> None:
        """Path.rmdir für genau `target` mit EBUSY scheitern lassen (Handle gehalten)."""
        original_rmdir = Path.rmdir

        def fake_rmdir(self):
            if self == target:
                e = OSError(errno.EBUSY, "EBUSY: directory handle held by another process")
                e.errno = errno.EBUSY
                raise e
            return original_rmdir(self)

        monkeypatch.setattr(Path, "rmdir", fake_rmdir)

    def test_skip_locked_reports_failure_when_own_handle_locked(self, tmp_path, monkeypatch):
        d = tmp_path / "emptylocked"
        d.mkdir()
        self._lock_rmdir(monkeypatch, d)

        ok, locked = _delete_dir_skip_locked(d)

        assert not ok, "Leeres, am Eigen-Handle gesperrtes Verzeichnis darf nicht als Erfolg gelten"
        assert locked == [], "Keine gesperrte Innendatei -> locked muss leer bleiben"
        assert d.exists(), "Verzeichnis existiert noch (rmdir scheiterte) -> kein Erfolg"

    def test_delete_path_reports_failure_and_retry_hint(self, tmp_path, monkeypatch):
        d = tmp_path / "busyempty"
        d.mkdir()

        # rmtree muss mit Lock-Fehler scheitern, damit der skip_locked-Pfad genommen wird
        def fake_rmtree(p, **kwargs):
            e = OSError(errno.EBUSY, "EBUSY")
            e.errno = errno.EBUSY
            raise e

        monkeypatch.setattr(ops, "_rmtree", fake_rmtree)
        self._lock_rmdir(monkeypatch, d)

        ok, msg = ops._delete_path(d)

        assert not ok, "_delete_path muss Fehlschlag melden (kein stilles completed)"
        assert d.exists()
        assert "handle" in msg.lower() or "retry" in msg.lower(), \
            f"Meldung soll Eigen-Handle-Lock/Retry benennen, war: '{msg}'"

    def test_chain_stays_pending_not_completed(self, tmp_path, monkeypatch):
        """execute_chain darf den Delete-Task NICHT als done markieren (-> Worker retryt)."""
        d = tmp_path / "queuedempty"
        d.mkdir()

        def fake_rmtree(p, **kwargs):
            e = OSError(errno.EBUSY, "EBUSY")
            e.errno = errno.EBUSY
            raise e

        monkeypatch.setattr(ops, "_rmtree", fake_rmtree)
        self._lock_rmdir(monkeypatch, d)

        task = Task(chain=[Step(op="delete", src=str(d))])
        result = ops.execute_chain(task)

        assert result is False, "Kette muss fehlschlagen solange das Handle gesperrt ist"
        assert task.status != "done", "Task darf nicht fälschlich 'done' sein"
        assert task.last_error, "last_error muss gesetzt sein (Grundlage für nächsten Retry)"
        assert d.exists()

    def test_succeeds_once_handle_released(self, tmp_path):
        """Gegenprobe: ohne Lock wird derselbe leere Ordner sauber gelöscht."""
        d = tmp_path / "freed"
        d.mkdir()
        ok, msg = ops._delete_path(d)
        assert ok, f"Ohne Lock muss der leere Ordner gelöscht werden: {msg}"
        assert not d.exists()
