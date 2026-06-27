"""Tests fuer P2 (Kontextmenue-Command) und P3 (Praeventiv-Waechter-Logik)."""
import subprocess
from pathlib import Path

from cloudlockfixer import contextmenu
from cloudlockfixer.providers import OneDriveProvider, SyncProvider
from cloudlockfixer.watcher import PreventiveWatcher


class FakeProvider(SyncProvider):
    name = "fake"

    def __init__(self):
        super().__init__()
        self.running = True
        self.paused = 0
        self.resumed = 0

    def _detect_roots(self):
        return []

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


def test_contextmenu_is_installed_checks_all_bases(monkeypatch):
    """Regression (Bug 9): is_installed() muss alle _BASES pruefen — nicht nur
    den ersten. Wenn BASES[0] fehlt aber BASES[1] vorhanden ist, muss True kommen."""
    import sys
    if sys.platform != "win32":
        return  # nur auf Windows ausfuehrbar (winreg existiert nicht auf Linux/Mac)
    import winreg
    from cloudlockfixer.contextmenu import _BASES, is_installed

    call_count = {"n": 0}

    class FakeKey:
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_open_key(root, path, *a, **k):
        call_count["n"] += 1
        # Erst-Aufruf (_BASES[0]) scheitert, zweiter (_BASES[1]) klappt
        if call_count["n"] == 1:
            raise OSError("nicht vorhanden")
        return FakeKey()

    monkeypatch.setattr(winreg, "OpenKey", fake_open_key)
    assert is_installed() is True, "Wenn BASES[1] vorhanden, muss is_installed() True sein"


def test_contextmenu_verb_key_no_double_backslash():
    """Regression: r'\\shell\\\\' erzeugte doppelten Backslash im Registry-Pfad."""
    from cloudlockfixer.contextmenu import _BASES, _OPS
    for base in _BASES:
        for key, _, _ in _OPS:
            vk = base + "\\shell\\" + key
            assert "\\\\" not in vk, f"Doppelter Backslash in Registry-Pfad: {vk!r}"


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


def test_dropbox_detect_roots_handles_non_dict_json(tmp_path, monkeypatch):
    """Regression (Bug 7): DropboxProvider._detect_roots darf nicht mit
    AttributeError crashen wenn info.json kein dict als Root hat."""
    from cloudlockfixer.providers import DropboxProvider
    info_dir = tmp_path / "Dropbox"
    info_dir.mkdir()
    info_json = info_dir / "info.json"
    monkeypatch.setenv("APPDATA", str(tmp_path))
    for bad in ("null", "[]", "42", '"string"'):
        info_json.write_text(bad, encoding="utf-8")
        prov = DropboxProvider()
        roots = prov._detect_roots()  # darf NICHT werfen
        assert isinstance(roots, list), f"Erwartet Liste fuer bad JSON={bad!r}"


def test_dropbox_detect_roots_handles_non_dict_section(tmp_path, monkeypatch):
    """Bug-Fix (Bug 11): info.json mit dict-Root, aber Section-Wert kein dict
    (z.B. {'personal': 'pfad-als-string'}) -> AttributeError beim .get('path')-Aufruf
    auf dem String. Muss leere Liste liefern, darf nicht werfen."""
    import json
    from cloudlockfixer.providers import DropboxProvider
    info_dir = tmp_path / "Dropbox"
    info_dir.mkdir()
    info_json = info_dir / "info.json"
    monkeypatch.setenv("APPDATA", str(tmp_path))
    # Section-Wert ist kein dict -> frueher AttributeError
    for bad_section in (
        {"personal": "nicht-ein-dict"},
        {"personal": 42},
        {"personal": ["list"]},
        {"personal": None},
    ):
        info_json.write_text(json.dumps(bad_section), encoding="utf-8")
        prov = DropboxProvider()
        roots = prov._detect_roots()
        assert isinstance(roots, list), (
            f"_detect_roots muss Liste liefern, nicht werfen: {bad_section!r}"
        )


def test_watcher_no_spurious_resume_if_pause_fails(monkeypatch):
    """Bug-Fix: wenn provider.pause() False zurückgibt (z.B. taskkill gescheitert),
    muss _paused_by_us auf False zurückgesetzt werden.

    Ohne den Fix: decide() setzt _paused_by_us=True, tick() ignoriert den
    pause()-Fehlschlag, nach Cooldown wird resume() auf einem nie-gestoppten
    Provider aufgerufen (spurious resume).
    """
    clock = [0.0]

    class FailPauseProvider(FakeProvider):
        def pause(self) -> bool:
            self.paused += 1
            return False  # Pause schlägt fehl (z.B. taskkill-Fehler)

    fail_prov = FailPauseProvider()
    w = PreventiveWatcher(fail_prov, threshold=3, cooldown_s=5,
                          time_fn=lambda: clock[0])
    monkeypatch.setattr(w, "count_recent_changes", lambda: 10)
    result = w.tick()
    assert result == "pause"  # decide() liefert "pause" (korrekt)
    assert not w._paused_by_us, (
        "_paused_by_us muss False sein wenn pause() scheiterte — "
        "sonst resume() nach Cooldown auf nie-gestoppten Provider"
    )
    # Kein spurious resume() nach Cooldown
    monkeypatch.setattr(w, "count_recent_changes", lambda: 0)
    clock[0] += 10
    result2 = w.tick()
    assert result2 != "resume", f"Spurious resume() nach fehlgeschlagenem pause(): {result2}"
    assert fail_prov.resumed == 0, "resume() darf nicht aufgerufen werden"


def test_watcher_counts_recent_files(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("y", encoding="utf-8")
    w = PreventiveWatcher(FakeProvider(), watch_dirs=[str(tmp_path)],
                          window_s=3600)
    assert w.count_recent_changes() >= 2


def test_tick_all_safe_against_concurrent_modification():
    """Regression: tick_all() muss list()-Snapshot nutzen -- sonst RuntimeError
    wenn ein Watcher waehrend der Iteration das dict modifiziert (simuliert
    Haupt-Thread, der self.watchers aendert).

    Dieser Test schlaegt fehl, wenn list() aus tick_all() entfernt wird."""
    from cloudlockfixer.watcher import tick_all

    watchers: dict = {}
    prov = FakeProvider()
    ticked = []

    class ModifyingWatcher(PreventiveWatcher):
        def tick(self):
            ticked.append(1)
            # Simuliert Haupt-Thread-Modifikation waehrend Iteration
            watchers["injected"] = PreventiveWatcher(FakeProvider(), watch_dirs=[])

    watchers["fake"] = ModifyingWatcher(prov, watch_dirs=[])

    # tick_all muss RuntimeError verhindern (list()-Snapshot)
    try:
        tick_all(watchers)
    except RuntimeError as e:
        assert False, f"tick_all() darf keinen RuntimeError erzeugen: {e}"

    assert ticked, "Watcher muss aufgerufen worden sein"


# ── Bug #BW-2: tick() ignoriert resume()-Rückgabewert ─────────────────────────

def test_watcher_tick_retries_resume_after_failure(monkeypatch):
    """Bug #BW-2: resume() Rückgabewert wurde in tick() ignoriert.
    Wenn resume() False zurückgibt, blieb _paused_by_us=False und der Provider
    pausierte dauerhaft bis zum App-Neustart — symmetrisch zum bereits behobenen
    pause()-Bug (v0.2.1 CHANGELOG).
    Fix: nach gescheitertem resume() _paused_by_us und _last_activity
    wiederherstellen, damit nach dem nächsten Cooldown ein Retry-Versuch erfolgt."""
    clock = [0.0]

    class FailResumeProvider(FakeProvider):
        resume_calls = 0

        def resume(self) -> bool:
            self.resume_calls += 1
            return False  # simuliert Prozess-Start-Fehler

    prov = FailResumeProvider()
    w = PreventiveWatcher(prov, threshold=3, cooldown_s=10,
                          time_fn=lambda: clock[0])

    # Phase 1: hohe Aktivität → pause() erfolgreich (FakeProvider.pause() gibt True)
    monkeypatch.setattr(w, "count_recent_changes", lambda: 10)
    assert w.tick() == "pause"
    assert w._paused_by_us

    # Phase 2: Cooldown abgewartet → resume() schlägt fehl
    monkeypatch.setattr(w, "count_recent_changes", lambda: 0)
    clock[0] += 11
    assert w.tick() == "resume"
    assert prov.resume_calls == 1

    # Kern-Assert: Zustand muss nach gescheitertem resume() wiederhergestellt sein
    assert w._paused_by_us, (
        "_paused_by_us muss nach gescheitertem resume() True sein — "
        "sonst bleibt der Provider dauerhaft pausiert"
    )
    assert w._last_activity is not None, (
        "_last_activity muss nach gescheitertem resume() gesetzt sein — "
        "sonst läuft kein neuer Cooldown und kein Retry erfolgt"
    )

    # Phase 3: zweiter Cooldown → resume() wird erneut versucht (Retry)
    clock[0] += 11
    assert w.tick() == "resume", (
        "Nach erneutem Cooldown muss resume() erneut versucht werden"
    )
    assert prov.resume_calls == 2, "resume() muss ein zweites Mal aufgerufen worden sein"
