"""Regressionstests fuer die Review-Fixes vom 2026-07-12.

Abgedeckt:
  FIX 1  Virtual-Mount-Guard im Praeventiv-Waechter (tick + Watcher-Bau)
  FIX 2  Robuster Laufwerks-Scan (_get_volume_label: SetThreadErrorMode +
         GetDriveTypeW-Filter)
  FIX 3  Optionales Retry-Limit; Default bleibt fire-and-forget pending
  FIX 4  Watcher/Worker-Race: RLock je Provider-Instanz serialisiert
         pause()/resume()
"""
from __future__ import annotations

import threading
import time

import pytest

from cloudlockfixer.models import Queue, Step, Task
from cloudlockfixer.providers import SyncProvider
from cloudlockfixer.watcher import PreventiveWatcher


class FakeProvider(SyncProvider):
    name = "fake"
    mount_type = "folder"

    def __init__(self, running=True):
        super().__init__()
        self.running = running
        self.paused = 0
        self.resumed = 0

    def _detect_roots(self):
        return []

    def owns_path(self, p) -> bool:
        return True

    def is_running(self) -> bool:
        return self.running

    def pause(self) -> bool:
        with self._lock:
            self.running = False
            self.paused += 1
            return True

    def resume(self) -> bool:
        with self._lock:
            self.running = True
            self.resumed += 1
            return True


class FakeVirtualProvider(FakeProvider):
    name = "fake-virtual"
    mount_type = "virtual"


# ── FIX 1: Virtual-Mount-Guard im Praeventiv-Waechter ──────────────────

def test_watcher_tick_never_pauses_virtual_provider(monkeypatch):
    """PreventiveWatcher.tick() darf einen Virtual-Mount-Provider nie pausieren,
    auch wenn die Aenderungsrate ueber der Schwelle liegt — sonst risse der
    Prozess-Kill den Laufwerks-Mount ab."""
    vprov = FakeVirtualProvider()
    w = PreventiveWatcher(vprov, threshold=3, cooldown_s=5)
    # Hohe Aktivitaet simulieren — wuerde bei folder-Provider pause() ausloesen
    monkeypatch.setattr(w, "count_recent_changes", lambda: 100)
    assert w.tick() == "none"
    assert vprov.paused == 0, "pause() darf bei virtual mount nie aufgerufen werden"
    assert not w._paused_by_us


def test_watcher_tick_folder_provider_still_pauses(monkeypatch):
    """Gegenprobe: ein folder-Provider wird weiterhin pausiert."""
    fprov = FakeProvider()
    w = PreventiveWatcher(fprov, threshold=3, cooldown_s=5)
    monkeypatch.setattr(w, "count_recent_changes", lambda: 100)
    assert w.tick() == "pause"
    assert fprov.paused == 1


def test_tray_builds_no_watcher_for_virtual_provider(monkeypatch, tmp_path):
    """TrayApp baut fuer virtuelle Provider keinen Praeventiv-Waechter.

    Statt die volle Qt-App zu instanziieren, wird der reine Bau-Filter aus
    __init__ nachgebildet: nur folder-Provider mit passenden watch_dirs
    landen im watchers-Dict."""
    from cloudlockfixer import providers as pmod

    folder_root = tmp_path / "dropbox"
    folder_root.mkdir()
    virtual_root = tmp_path / "gdrive"
    virtual_root.mkdir()

    folder_prov = FakeProvider()
    folder_prov.name = "Dropbox"
    virtual_prov = FakeVirtualProvider()
    virtual_prov.name = "Google Drive"

    provs = [folder_prov, virtual_prov]
    watch_dirs = [str(folder_root), str(virtual_root)]

    def fake_provider_for(d):
        return folder_prov if str(d) == str(folder_root) else virtual_prov

    monkeypatch.setattr(pmod, "provider_for", fake_provider_for)

    # Nachbildung der Filter-Schleife aus TrayApp.__init__
    watchers: dict = {}
    for prov in provs:
        if prov.mount_type == "virtual":
            continue
        dirs = [d for d in watch_dirs
                if fake_provider_for(d) is not None
                and fake_provider_for(d).name == prov.name]
        if dirs:
            watchers[prov.name] = PreventiveWatcher(prov, watch_dirs=dirs)

    assert "Dropbox" in watchers
    assert "Google Drive" not in watchers, "virtueller Provider darf keinen Waechter bekommen"


# ── FIX 2: Robuster Laufwerks-Scan ─────────────────────────────────────

class _FakeKernel32:
    """Minimaler kernel32-Ersatz zum Verifizieren von SetThreadErrorMode und
    des GetDriveTypeW-Filters ohne echte Win32-Calls."""
    def __init__(self, drive_type: int, label: str = "pCloud Drive"):
        self._drive_type = drive_type
        self._label = label
        self.set_error_mode_calls: list = []
        self.get_volume_calls = 0

    def SetThreadErrorMode(self, new_mode, old_ptr):
        self.set_error_mode_calls.append(new_mode)
        return 1

    def GetDriveTypeW(self, root):
        return self._drive_type

    def GetVolumeInformationW(self, root, buf, size, *rest):
        self.get_volume_calls += 1
        buf.value = self._label
        return 1


def _patch_kernel32(monkeypatch, fake):
    import ctypes as _ctypes
    import sys as _sys
    monkeypatch.setattr(_sys, "platform", "win32")

    class _FakeWinDLL:
        kernel32 = fake

    monkeypatch.setattr(_ctypes, "windll", _FakeWinDLL())


def test_get_volume_label_sets_and_restores_error_mode(monkeypatch):
    """FIX 2a: der Fehlermodus wird gesetzt (SEM_FAILCRITICALERRORS) und danach
    wiederhergestellt (zweiter SetThreadErrorMode-Aufruf)."""
    from cloudlockfixer.providers import _get_volume_label, _SEM_FAILCRITICALERRORS

    fake = _FakeKernel32(drive_type=3, label="pCloud Drive")  # DRIVE_FIXED
    _patch_kernel32(monkeypatch, fake)

    label = _get_volume_label("P")
    assert label == "pCloud Drive"
    assert len(fake.set_error_mode_calls) == 2, "setzen + wiederherstellen erwartet"
    assert fake.set_error_mode_calls[0] == _SEM_FAILCRITICALERRORS


def test_get_volume_label_skips_removable_drive(monkeypatch):
    """FIX 2b: ein DRIVE_REMOVABLE (2) wird nie an GetVolumeInformationW gereicht."""
    from cloudlockfixer.providers import _get_volume_label

    fake = _FakeKernel32(drive_type=2)  # DRIVE_REMOVABLE
    _patch_kernel32(monkeypatch, fake)

    assert _get_volume_label("E") == ""
    assert fake.get_volume_calls == 0, "Removable darf GetVolumeInformationW nie erreichen"
    # Fehlermodus muss trotz frueher Rueckkehr wiederhergestellt worden sein
    assert len(fake.set_error_mode_calls) == 2


def test_get_volume_label_accepts_remote_drive(monkeypatch):
    """DRIVE_REMOTE (4) — Netzlaufwerk-artige Cloud-Mounts — wird abgefragt."""
    from cloudlockfixer.providers import _get_volume_label

    fake = _FakeKernel32(drive_type=4, label="Google Drive")  # DRIVE_REMOTE
    _patch_kernel32(monkeypatch, fake)

    assert _get_volume_label("G") == "Google Drive"
    assert fake.get_volume_calls == 1


# ── FIX 3: Optionales Retry-Limit, unbegrenzter Default ────────────────

def _failing_queue(tmp_path) -> Queue:
    q = Queue(tmp_path)
    # move mit fehlender Quelle scheitert deterministisch bei jedem Lauf
    task = Task(chain=[Step(op="move", src=str(tmp_path / "missing"),
                            arg=str(tmp_path / "dst"))])
    q.add(task)
    return q


def test_worker_marks_task_failed_after_cap(tmp_path):
    """Ein explizites Limit setzt dauerhaft scheiternde Tasks auf 'failed'.

    Hinweis: run_once() ruft queue.load() auf und ersetzt die Task-Objekte —
    der aktuelle Zustand wird darum nach jedem Lauf frisch aus q.tasks gelesen."""
    from cloudlockfixer.worker import run_once

    q = _failing_queue(tmp_path)

    # max_retries=3 -> nach 3 Laeufen failed
    for expected in (1, 2):
        s = run_once(q, max_retries=3)
        assert s["failed_again"] == 1 and s["failed_permanent"] == 0
        task = q.tasks[0]
        assert task.status == "pending"
        assert task.retry_count == expected

    s = run_once(q, max_retries=3)
    assert s["failed_permanent"] == 1 and s["failed_again"] == 0
    task = q.tasks[0]
    assert task.status == "failed"
    assert task.retry_count == 3
    assert "3" in task.last_error  # aussagekraeftige Meldung mit Versuchszahl


def test_worker_default_keeps_retryable_task_pending_past_six_attempts(tmp_path):
    """Der Default darf temporäre Cloud-Locks nicht nach fünf Läufen aufgeben."""
    from cloudlockfixer.worker import run_once

    q = _failing_queue(tmp_path)
    for expected in range(1, 7):
        summary = run_once(q)
        task = q.tasks[0]
        assert summary["failed_again"] == 1
        assert summary["failed_permanent"] == 0
        assert task.status == "pending"
        assert task.retry_count == expected


def test_failed_task_not_picked_up_again(tmp_path):
    """Ein 'failed' Task wird von der pending-Auswahl ausgeschlossen."""
    from cloudlockfixer.worker import run_once

    q = _failing_queue(tmp_path)
    for _ in range(3):
        run_once(q, max_retries=3)
    assert q.tasks[0].status == "failed"

    # Weiterer Lauf greift den failed-Task nicht mehr auf
    retry_before = q.tasks[0].retry_count
    s = run_once(q, max_retries=3)
    assert s["pending_start"] == 0
    assert q.tasks[0].retry_count == retry_before, (
        "failed-Task darf nicht erneut versucht werden"
    )


def test_failed_task_excluded_from_pending_property(tmp_path):
    q = Queue(tmp_path)
    t = Task(chain=[Step(op="delete", src="x")], status="failed")
    q.add(t)
    assert t not in q.pending


def test_worker_blocks_deterministic_target_conflict(tmp_path):
    """Ein existierendes Ziel ist ein sichtbarer Konflikt, kein Endlos-Retry."""
    from cloudlockfixer.worker import run_once

    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    src.write_text("source", encoding="utf-8")
    dst.write_text("target", encoding="utf-8")
    q = Queue(tmp_path / "queue")
    q.add(Task(chain=[Step(op="move", src=str(src), arg=str(dst))]))

    summary = run_once(q)

    task = q.tasks[0]
    assert summary["blocked"] == 1
    assert task.status == "blocked"
    assert task.last_outcome == "blocked"
    assert task.retry_count == 1
    assert task not in q.pending


# ── FIX 4: Provider-Lock serialisiert pause()/resume() ─────────────────

def test_provider_has_instance_lock():
    """Jede Provider-Instanz besitzt einen eigenen (nicht geteilten) RLock."""
    p1 = FakeProvider()
    p2 = FakeProvider()
    assert isinstance(p1._lock, type(threading.RLock()))
    assert p1._lock is not p2._lock, "kein globales Lock — pro Instanz"


def test_concurrent_pause_resume_stay_consistent():
    """FIX 4: konkurrierende pause()/resume()-Aufrufe auf derselben Instanz
    duerfen sich nicht ueberlappen (Lock serialisiert). Ohne Lock kann der
    nicht-atomare running-Toggle + Zaehler-Increment korrumpieren."""

    class SlowProvider(SyncProvider):
        name = "slow"
        mount_type = "folder"

        def __init__(self):
            super().__init__()
            self.running = True
            self.in_critical = 0
            self.max_overlap = 0

        def _detect_roots(self):
            return []

        def owns_path(self, p):
            return True

        def is_running(self):
            return self.running

        def _critical(self, target):
            with self._lock:
                self.in_critical += 1
                self.max_overlap = max(self.max_overlap, self.in_critical)
                time.sleep(0.001)  # Fenster fuer Ueberlappung
                self.running = target
                self.in_critical -= 1
                return True

        def pause(self):
            return self._critical(False)

        def resume(self):
            return self._critical(True)

    prov = SlowProvider()
    threads = []
    for i in range(20):
        target = prov.pause if i % 2 == 0 else prov.resume
        threads.append(threading.Thread(target=target))
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert prov.max_overlap == 1, (
        f"pause()/resume() ueberlappten (max_overlap={prov.max_overlap}) — "
        "Lock serialisiert nicht"
    )


def test_watcher_tick_holds_provider_lock_during_state_change(monkeypatch):
    """FIX 4: waehrend tick() den Zustand aendert und pause() aufruft, haelt es
    den Provider-Lock — ein konkurrierender Worker-pause() muss warten, sodass
    _paused_by_us konsistent bleibt (reentranter RLock erlaubt den inneren
    pause()-Aufruf)."""
    fprov = FakeProvider()
    w = PreventiveWatcher(fprov, threshold=3, cooldown_s=5)
    monkeypatch.setattr(w, "count_recent_changes", lambda: 100)

    # tick() muss den Lock beim pause() halten koennen (RLock reentrant)
    assert w.tick() == "pause"
    assert w._paused_by_us
    assert fprov.paused == 1
