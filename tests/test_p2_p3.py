"""Tests fuer P2 (Kontextmenue-Command) und P3 (Praeventiv-Waechter-Logik)."""
import subprocess
from pathlib import Path

from cloudlockfixer import contextmenu
from cloudlockfixer.providers import OneDriveProvider, SyncProvider
from cloudlockfixer.watcher import PreventiveWatcher


class FakeProvider(SyncProvider):
    name = "fake"

    def __init__(self):
        self.running = True
        self.paused = 0
        self.resumed = 0

    def owns_path(self, p) -> bool:
        return True

    def is_running(self) -> bool:
        return self.running

    def pause(self) -> bool:
        self.running = False
        self.paused += 1
        return True

    def resume(self) -> bool:
        self.running = True
        self.resumed += 1
        return True


# ── P2 ──────────────────────────────────────────────────────────────

def test_contextmenu_command_format():
    cmd = contextmenu._command("rename")
    assert "gui-add" in cmd
    assert "--op rename" in cmd
    assert '--src "%1"' in cmd
    assert "clf_launcher.pyw" in cmd


# ── P3: reine Entscheidungslogik ────────────────────────────────────

def test_watcher_decide_pause_then_resume_after_cooldown():
    clock = [1000.0]
    prov = FakeProvider()
    w = PreventiveWatcher(prov, threshold=5, cooldown_s=10,
                          time_fn=lambda: clock[0])
    assert w.decide(2) == "none"          # unter Schwelle
    assert not w._paused_by_us
    assert w.decide(5) == "pause"         # Schwelle erreicht
    assert w._paused_by_us
    assert w.decide(3) == "none"          # weiter Aktivitaet -> bleibt pausiert
    clock[0] += 5
    assert w.decide(0) == "none"          # ruhig, aber Cooldown nicht erreicht
    clock[0] += 6                         # 11s seit letzter Aktivitaet (>10)
    assert w.decide(0) == "resume"
    assert not w._paused_by_us


def test_watcher_tick_pauses_and_resumes(monkeypatch):
    clock = [0.0]
    prov = FakeProvider()
    w = PreventiveWatcher(prov, threshold=3, cooldown_s=5,
                          time_fn=lambda: clock[0])
    monkeypatch.setattr(w, "count_recent_changes", lambda: 10)
    assert w.tick() == "pause"
    assert prov.paused == 1 and not prov.running
    monkeypatch.setattr(w, "count_recent_changes", lambda: 0)
    clock[0] += 6
    assert w.tick() == "resume"
    assert prov.resumed == 1 and prov.running


def test_watcher_no_resume_if_provider_already_stopped(monkeypatch):
    """Regression: wenn decide 'pause' sagt, der Provider aber schon gestoppt
    ist (User hat ihn manuell beendet), darf spaeter KEIN resume erfolgen."""
    clock = [0.0]
    prov = FakeProvider()
    prov.running = False  # User hat OneDrive manuell beendet
    w = PreventiveWatcher(prov, threshold=3, cooldown_s=5,
                          time_fn=lambda: clock[0])
    monkeypatch.setattr(w, "count_recent_changes", lambda: 10)
    assert w.tick() == "pause"
    assert prov.paused == 0, "Provider war schon gestoppt — pause() darf nicht aufgerufen werden"
    assert not w._paused_by_us, "_paused_by_us muss zurueckgesetzt sein"
    monkeypatch.setattr(w, "count_recent_changes", lambda: 0)
    clock[0] += 6
    assert w.tick() == "none", "Kein resume, da wir nicht pausiert haben"
    assert prov.resumed == 0


# ── Provider-Robustheit (Regression: deutsches Windows tasklist-Encoding) ──

class _FakeCompleted:
    def __init__(self, stdout):
        self.stdout = stdout


def test_is_running_handles_none_stdout(monkeypatch):
    """Auf de-Windows kann die dekodierte tasklist-Ausgabe None sein
    (UnicodeDecodeError im Reader-Thread) -> darf NICHT mit TypeError crashen."""
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(None))
    assert OneDriveProvider().is_running() is False


def test_is_running_detects_process(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("OneDrive.exe  1234 Console\n"))
    assert OneDriveProvider().is_running() is True


def test_watcher_counts_recent_files(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("y", encoding="utf-8")
    w = PreventiveWatcher(FakeProvider(), watch_dirs=[str(tmp_path)],
                          window_s=3600)
    assert w.count_recent_changes() >= 2
