"""Cross-platform provider abstraction tests for CloudLockFixer (Linux & macOS)."""
from __future__ import annotations

import json
from pathlib import Path

import cloudlockfixer.providers as providers
from cloudlockfixer.providers import (
    BoxProvider,
    DropboxProvider,
    GoogleDriveProvider,
    ICloudProvider,
    NextcloudProvider,
    OneDriveProvider,
    PCloudProvider,
    SynologyDriveProvider,
    _check_process,
    _kill_process,
    _get_posix_patterns,
)


class _FakeCompleted:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


# ── Process Pattern and Check Tests (POSIX) ───────────────────────


def test_posix_pattern_mapping():
    assert "Google Drive" in _get_posix_patterns("GoogleDriveFS.exe")
    assert "OneDrive" in _get_posix_patterns("OneDrive.exe")
    assert "Dropbox" in _get_posix_patterns("Dropbox.exe")
    assert "bird" in _get_posix_patterns("iCloudDrive.exe")
    assert _get_posix_patterns("custom.exe") == ["custom"]


def test_check_process_posix_pgrep_success(monkeypatch):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    monkeypatch.setattr(
        providers.subprocess,
        "run",
        lambda cmd, **k: _FakeCompleted(stdout="1234\n", returncode=0),
    )
    assert _check_process("OneDrive.exe") is True


def test_check_process_posix_pgrep_failure_and_no_proc(monkeypatch):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(
        providers.subprocess,
        "run",
        lambda cmd, **k: _FakeCompleted(stdout="", returncode=1),
    )
    assert _check_process("OneDrive.exe") is False


def test_check_process_posix_proc_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "linux")

    # pgrep fails with OSError (e.g. command not found)
    def fake_run(cmd, **k):
        raise OSError("pgrep not found")

    monkeypatch.setattr(providers.subprocess, "run", fake_run)

    # create fake /proc structure
    proc = tmp_path / "proc"
    pid_dir = proc / "456"
    pid_dir.mkdir(parents=True)
    (pid_dir / "cmdline").write_bytes(b"/usr/bin/onedrive\x00--monitor\x00")

    monkeypatch.setattr(providers, "Path", lambda *args: proc if args == ("/proc",) else Path(*args))

    assert _check_process("OneDrive.exe") is True


def test_kill_process_posix(monkeypatch):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    calls = []

    def fake_run(cmd, **k):
        calls.append(cmd)
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(providers.subprocess, "run", fake_run)
    monkeypatch.setattr(providers.time, "sleep", lambda s: None)
    monkeypatch.setattr(providers, "_check_process", lambda exe: False)

    assert _kill_process("OneDrive.exe") is True
    assert any(c[0] == "pkill" for c in calls)


# ── macOS Root Discovery Tests ────────────────────────────────────


def test_macos_onedrive_cloudstorage_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cs = tmp_path / "Library" / "CloudStorage"
    od_personal = cs / "OneDrive-Personal"
    od_work = cs / "OneDrive-Contoso"
    od_personal.mkdir(parents=True)
    od_work.mkdir(parents=True)

    prov = OneDriveProvider()
    roots = prov._detect_roots()
    assert od_personal in roots
    assert od_work in roots


def test_macos_googledrive_cloudstorage_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cs = tmp_path / "Library" / "CloudStorage"
    gd = cs / "GoogleDrive-user@example.com"
    gd.mkdir(parents=True)

    prov = GoogleDriveProvider()
    roots = prov._detect_roots()
    assert gd in roots


def test_macos_dropbox_application_support_and_cloudstorage(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    app_support = tmp_path / "Library" / "Application Support" / "Dropbox"
    app_support.mkdir(parents=True)
    info = app_support / "info.json"
    sync_dir = tmp_path / "CustomDropbox"
    sync_dir.mkdir(parents=True)
    info.write_text(json.dumps({"personal": {"path": str(sync_dir)}}), encoding="utf-8")

    cs = tmp_path / "Library" / "CloudStorage"
    cs_db = cs / "Dropbox"
    cs_db.mkdir(parents=True)

    prov = DropboxProvider()
    roots = prov._detect_roots()
    assert sync_dir in roots
    assert cs_db in roots


def test_macos_box_cloudstorage_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cs = tmp_path / "Library" / "CloudStorage"
    box_personal = cs / "Box-Box"
    box_personal.mkdir(parents=True)

    prov = BoxProvider()
    roots = prov._detect_roots()
    assert box_personal in roots


def test_macos_nextcloud_preferences_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    prefs = tmp_path / "Library" / "Preferences" / "Nextcloud"
    prefs.mkdir(parents=True)
    sync_dir = tmp_path / "NextcloudSync"
    sync_dir.mkdir(parents=True)
    (prefs / "nextcloud.cfg").write_text(
        f"0\\FoldersWithPlaceholders\\1\\localPath={sync_dir.as_posix()}/\n",
        encoding="utf-8",
    )

    prov = NextcloudProvider()
    roots = prov._detect_roots()
    assert sync_dir in roots


def test_macos_icloud_mobile_documents_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cloud_docs = tmp_path / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    cloud_docs.mkdir(parents=True)

    prov = ICloudProvider()
    roots = prov._detect_roots()
    assert cloud_docs in roots


def test_posix_pcloud_home_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    pcloud_dir = tmp_path / "pCloudDrive"
    pcloud_dir.mkdir(parents=True)

    prov = PCloudProvider()
    roots = prov._detect_roots()
    assert pcloud_dir in roots


# ── Linux Root Discovery Tests ───────────────────────────────────


def test_linux_dropbox_dotfile_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)

    dot_db = tmp_path / ".dropbox"
    dot_db.mkdir(parents=True)
    sync_dir = tmp_path / "DropboxLinux"
    sync_dir.mkdir(parents=True)
    (dot_db / "info.json").write_text(
        json.dumps({"personal": {"path": str(sync_dir)}}),
        encoding="utf-8",
    )

    prov = DropboxProvider()
    roots = prov._detect_roots()
    assert sync_dir in roots


def test_linux_nextcloud_xdg_config_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)

    xdg_cfg = tmp_path / "xdg_config"
    nc_cfg_dir = xdg_cfg / "Nextcloud"
    nc_cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_cfg))

    sync_dir = tmp_path / "NextcloudLinux"
    sync_dir.mkdir(parents=True)
    (nc_cfg_dir / "nextcloud.cfg").write_text(
        f"0\\FoldersWithPlaceholders\\1\\localPath={sync_dir.as_posix()}/\n",
        encoding="utf-8",
    )

    prov = NextcloudProvider()
    roots = prov._detect_roots()
    assert sync_dir in roots


def test_linux_synology_dotfile_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    syno_dir = tmp_path / ".SynologyDrive" / "data" / "session" / "1"
    syno_dir.mkdir(parents=True)
    sync_dir = tmp_path / "SynologySyncLinux"
    sync_dir.mkdir(parents=True)

    (syno_dir / "conf").write_text(
        f'local_path = "{sync_dir.as_posix()}"\n',
        encoding="utf-8",
    )

    prov = SynologyDriveProvider()
    roots = prov._detect_roots()
    assert sync_dir in roots


# ── Cross-Platform Resume Tests ──────────────────────────────────


def test_macos_resume_invokes_open(monkeypatch):
    monkeypatch.setattr(providers.sys, "platform", "darwin")
    calls = []
    monkeypatch.setattr(
        providers.subprocess,
        "Popen",
        lambda cmd, **k: calls.append(cmd),
    )

    prov = OneDriveProvider()
    assert prov.resume() is True
    assert calls[-1] == ["open", "-a", "OneDrive"]

    prov_gd = GoogleDriveProvider()
    assert prov_gd.resume() is True
    assert calls[-1] == ["open", "-a", "Google Drive"]

    prov_nc = NextcloudProvider()
    assert prov_nc.resume() is True
    assert calls[-1] == ["open", "-a", "Nextcloud"]


def test_linux_resume_invokes_binary(monkeypatch):
    monkeypatch.setattr(providers.sys, "platform", "linux")
    monkeypatch.setattr(providers.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    calls = []
    monkeypatch.setattr(
        providers.subprocess,
        "Popen",
        lambda cmd, **k: calls.append(cmd),
    )

    prov = OneDriveProvider()
    assert prov.resume() is True
    assert calls[-1] == ["/usr/bin/onedrive", "--monitor"]

    prov_db = DropboxProvider()
    assert prov_db.resume() is True
    assert calls[-1] == ["/usr/bin/dropbox", "start"]

    prov_nc = NextcloudProvider()
    assert prov_nc.resume() is True
    assert calls[-1] == ["/usr/bin/nextcloud", "--background"]
