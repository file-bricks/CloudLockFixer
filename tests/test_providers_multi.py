"""Tests für Multicloud-Provider: Discovery, Erkennung, Virtual-Mount Guard."""
import subprocess
from pathlib import Path
from unittest.mock import patch

from cloudlockfixer.providers import (
    BoxProvider, DropboxProvider, GoogleDriveProvider, ICloudProvider, NextcloudProvider, OneDriveProvider,
    SyncProvider, _discover_providers, _get_providers, _is_subpath,
    available_providers, provider_for,
)
from cloudlockfixer.worker import _providers_to_pause
from cloudlockfixer.models import Step, Task


class FakeProvider(SyncProvider):
    name = "fake"
    mount_type = "folder"

    def __init__(self, roots=None, running=True):
        super().__init__()
        self._fake_roots = roots or []
        self.running = running
        self._cached_roots = self._fake_roots

    def _detect_roots(self):
        return self._fake_roots

    def owns_path(self, p):
        return any(_is_subpath(Path(p), r) for r in self._fake_roots)

    def is_running(self):
        return self.running

    def pause(self):
        self.running = False
        return True

    def resume(self):
        self.running = True
        return True


class FakeVirtualProvider(FakeProvider):
    name = "fake-virtual"
    mount_type = "virtual"


# ── Provider-Attribute ─────────────────────────────────────────────

def test_onedrive_is_folder_type():
    assert OneDriveProvider().mount_type == "folder"


def test_googledrive_is_virtual_type():
    assert GoogleDriveProvider().mount_type == "virtual"


def test_dropbox_is_folder_type():
    assert DropboxProvider().mount_type == "folder"


def test_box_is_folder_type():
    assert BoxProvider().mount_type == "folder"


def test_nextcloud_is_folder_type():
    assert NextcloudProvider().mount_type == "folder"


def test_icloud_is_folder_type():
    assert ICloudProvider().mount_type == "folder"


# ── Discovery ──────────────────────────────────────────────────────

def test_discover_includes_provider_with_roots(monkeypatch, tmp_path):
    root = tmp_path / "FakeCloud"
    root.mkdir()
    monkeypatch.setattr(DropboxProvider, "_roots", lambda self: [root])
    providers = _discover_providers()
    names = [p.name for p in providers]
    assert "Dropbox" in names


def test_discover_excludes_provider_without_roots(monkeypatch):
    monkeypatch.setattr(ICloudProvider, "_roots", lambda self: [])
    providers = _discover_providers()
    names = [p.name for p in providers]
    assert "iCloud" not in names


# ── owns_path ──────────────────────────────────────────────────────

def test_onedrive_owns_path(monkeypatch, tmp_path):
    root = tmp_path / "OneDrive"
    root.mkdir()
    (root / "sub").mkdir()
    monkeypatch.setattr(OneDriveProvider, "_roots", lambda self: [root])
    prov = OneDriveProvider()
    assert prov.owns_path(root / "sub")
    assert not prov.owns_path(tmp_path / "other")


def test_dropbox_owns_path_via_info_json(monkeypatch, tmp_path):
    root = tmp_path / "MyDropbox"
    root.mkdir()
    monkeypatch.setattr(DropboxProvider, "_roots", lambda self: [root])
    prov = DropboxProvider()
    assert prov.owns_path(root / "file.txt")


def test_box_detects_custom_root_from_registry(monkeypatch, tmp_path):
    custom_root = tmp_path / "CustomCloud" / "Box"
    custom_root.mkdir(parents=True)
    monkeypatch.setattr("cloudlockfixer.providers._read_box_custom_location", lambda: custom_root)
    prov = BoxProvider()
    roots = prov._detect_roots()
    assert custom_root in roots


def test_nextcloud_detects_roots_from_cfg(monkeypatch, tmp_path):
    appdata = tmp_path / "AppData" / "Roaming"
    cfg_dir = appdata / "Nextcloud"
    cfg_dir.mkdir(parents=True)
    synced_root = tmp_path / "Nextcloud"
    synced_root.mkdir()
    cfg_dir.joinpath("nextcloud.cfg").write_text(
        "[Accounts]\n"
        "0\\FoldersWithPlaceholders\\1\\localPath="
        f"{synced_root.as_posix()}/\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("APPDATA", str(appdata))
    prov = NextcloudProvider()
    roots = prov._detect_roots()
    assert synced_root in roots


# ── is_running (mocked) ───────────────────────────────────────────

class _FakeCompleted:
    def __init__(self, stdout):
        self.stdout = stdout


def test_googledrive_is_running_detects_process(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("GoogleDriveFS.exe  9008\n"))
    assert GoogleDriveProvider().is_running() is True


def test_googledrive_is_running_negative(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("INFO: Keine Aufgaben\n"))
    assert GoogleDriveProvider().is_running() is False


def test_dropbox_is_running(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("Dropbox.exe  1234\n"))
    assert DropboxProvider().is_running() is True


def test_box_is_running(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("Box.exe  2345\n"))
    assert BoxProvider().is_running() is True


def test_nextcloud_is_running(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("nextcloud.exe  6789\n"))
    assert NextcloudProvider().is_running() is True


def test_icloud_is_running_either_process(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted("iCloud.exe  5678\n"))
    assert ICloudProvider().is_running() is True


# ── Virtual-mount Pause Guard ──────────────────────────────────────

def test_virtual_mount_provider_skipped_in_pause(tmp_path):
    vroot = tmp_path / "gdrive"
    vroot.mkdir()
    vprov = FakeVirtualProvider(roots=[vroot], running=True)
    task = Task(chain=[Step(op="move", src=str(vroot / "a"), arg=str(tmp_path / "b"))])
    task.retry_count = 10

    with patch("cloudlockfixer.worker.provider_for", return_value=vprov):
        result = _providers_to_pause([task], force_pause=True)

    assert vprov not in result


def test_folder_mount_provider_included_in_pause(tmp_path):
    froot = tmp_path / "dropbox"
    froot.mkdir()
    fprov = FakeProvider(roots=[froot], running=True)
    task = Task(chain=[Step(op="delete", src=str(froot / "x"))])
    task.retry_count = 10

    with patch("cloudlockfixer.worker.provider_for", return_value=fprov):
        result = _providers_to_pause([task], force_pause=True)

    assert fprov in result


# ── provider_for with multiple providers ───────────────────────────

def test_provider_for_returns_correct_provider(monkeypatch, tmp_path):
    od_root = tmp_path / "OneDrive"
    od_root.mkdir()
    db_root = tmp_path / "Dropbox"
    db_root.mkdir()
    bx_root = tmp_path / "Box"
    bx_root.mkdir()
    nc_root = tmp_path / "Nextcloud"
    nc_root.mkdir()
    monkeypatch.setattr(OneDriveProvider, "_roots", lambda self: [od_root])
    monkeypatch.setattr(DropboxProvider, "_roots", lambda self: [db_root])
    monkeypatch.setattr(BoxProvider, "_roots", lambda self: [bx_root])
    monkeypatch.setattr(NextcloudProvider, "_roots", lambda self: [nc_root])
    monkeypatch.setattr(GoogleDriveProvider, "_roots", lambda self: [])
    monkeypatch.setattr(ICloudProvider, "_roots", lambda self: [])

    import cloudlockfixer.providers as pmod
    old = pmod._PROVIDERS
    pmod._PROVIDERS = _discover_providers()
    try:
        p1 = provider_for(od_root / "file.txt")
        assert p1 is not None and p1.name == "OneDrive"
        p2 = provider_for(db_root / "doc.pdf")
        assert p2 is not None and p2.name == "Dropbox"
        p3 = provider_for(bx_root / "slides.pptx")
        assert p3 is not None and p3.name == "Box"
        p4 = provider_for(nc_root / "photo.jpg")
        assert p4 is not None and p4.name == "Nextcloud"
        p5 = provider_for(tmp_path / "unrelated")
        assert p5 is None
    finally:
        pmod._PROVIDERS = old  # restore cache


# ── available_providers ────────────────────────────────────────────

def test_available_providers_returns_list():
    result = available_providers()
    assert isinstance(result, list)
    assert all(isinstance(p, SyncProvider) for p in result)


# ── Bug #BW-1: GoogleDrive resume() — semantische Versionssortierung ──────────

def test_googledrive_version_sort_key_is_semantic():
    """Bug #BW-1: sorted(glob, reverse=True) nutzt lexikografische Sortierung;
    '9.0.0' > '62.0.1' als String — '9' > '6' zeichenweise. Numerisch gilt
    62 > 9. Die extrahierte _gdrive_version_key-Funktion muss integer-basiert
    sortieren."""
    from cloudlockfixer.providers import _gdrive_version_key

    paths = [
        Path("9.0.0") / "GoogleDriveFS.exe",
        Path("62.0.1") / "GoogleDriveFS.exe",
        Path("8.99.9") / "GoogleDriveFS.exe",
    ]
    ordered = sorted(paths, key=_gdrive_version_key, reverse=True)
    names = [p.parent.name for p in ordered]
    assert names == ["62.0.1", "9.0.0", "8.99.9"], (
        f"Erwartet semantische Reihenfolge [62.0.1, 9.0.0, 8.99.9], war: {names}"
    )


def test_googledrive_resume_picks_highest_semantic_version(tmp_path, monkeypatch):
    """Integration: resume() muss die semantisch höchste Version zuerst versuchen.
    Bug #BW-1: ohne Fix startet lexikografisches '9.0.0' vor semantisch höherem '62.0.1'."""
    import subprocess as sp

    base = tmp_path / "Drive File Stream"
    for ver in ("9.0.0", "62.0.1", "8.99.9"):
        (base / ver).mkdir(parents=True)
        (base / ver / "GoogleDriveFS.exe").write_text("x", encoding="utf-8")

    started: list[str] = []

    def fake_popen(cmd):
        started.append(Path(cmd[0]).parent.name)
        raise OSError("Testumgebung: kein echter Start")

    monkeypatch.setattr(sp, "Popen", fake_popen)
    monkeypatch.setattr(GoogleDriveProvider, "_RESUME_BASE", base, raising=False)

    GoogleDriveProvider().resume()

    assert started, "Popen wurde nicht aufgerufen — _RESUME_BASE-Patch prüfen"
    assert started[0] == "62.0.1", (
        f"Höchste semantische Version '62.0.1' muss zuerst versucht werden, "
        f"war: {started[0]!r}"
    )


# ── Robustheit: _check_process() — Groß-/Kleinschreibung ──────────────────────

def test_check_process_case_insensitive_exe_name(monkeypatch):
    """Robustheit: tasklist gibt Prozessnamen in System-Schreibweise zurück
    (z.B. 'Nextcloud.exe'). Wenn wir mit 'nextcloud.exe' suchen, muss der
    Vergleich trotzdem True liefern (case-insensitive)."""
    from cloudlockfixer.providers import _check_process

    class _Fake:
        stdout = "Nextcloud.exe  6789 Console   1   5.564 K\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Fake())

    # Suche mit Kleinbuchstaben — muss True ergeben trotz Groß-N in der Ausgabe
    assert _check_process("nextcloud.exe") is True, (
        "case-insensitive Suche muss Treffer finden wenn Ausgabe 'Nextcloud.exe' enthält"
    )
