"""Tests for cross-platform process management abstraction (Task 169)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

from cloudlockfixer.process import (
    ProcessManager,
    check_process,
    get_posix_patterns,
    kill_process,
    launch_process,
)


def test_get_posix_patterns_known_aliases():
    assert "Google Drive" in get_posix_patterns("GoogleDriveFS.exe")
    assert "onedrive" in get_posix_patterns("OneDrive.exe")
    assert "dropbox" in get_posix_patterns("Dropbox.exe")
    assert "box" in get_posix_patterns("Box.exe")
    assert "nextcloud" in get_posix_patterns("Nextcloud.exe")
    assert "pcloud" in get_posix_patterns("pCloud.exe")
    assert "synology-drive" in get_posix_patterns("cloud-drive-ui.exe")
    assert "bird" in get_posix_patterns("iCloudDrive.exe")


def test_get_posix_patterns_fallback():
    assert get_posix_patterns("customsync.exe") == ["customsync"]
    assert get_posix_patterns("customdaemon") == ["customdaemon"]


def test_check_process_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    mock_runner = MagicMock()
    mock_runner.return_value.stdout = "OneDrive.exe                 1234 Console"

    assert check_process("OneDrive.exe", _runner=mock_runner) is True
    assert check_process("Dropbox.exe", _runner=mock_runner) is False

    mock_runner.side_effect = OSError("command failed")
    assert check_process("OneDrive.exe", _runner=mock_runner) is False


def test_check_process_posix_pgrep(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")

    mock_runner = MagicMock()
    # Return success for pgrep
    mock_runner.return_value.returncode = 0
    mock_runner.return_value.stdout = "4567\n"

    assert check_process("OneDrive.exe", _runner=mock_runner) is True
    assert mock_runner.call_args[0][0][:2] == ["pgrep", "-f"]


def test_check_process_linux_proc_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")

    # pgrep fails
    mock_runner = MagicMock()
    mock_runner.return_value.returncode = 1
    mock_runner.return_value.stdout = ""

    # create fake /proc directory
    fake_proc = tmp_path / "proc"
    fake_proc.mkdir()
    pid_dir = fake_proc / "1234"
    pid_dir.mkdir()
    (pid_dir / "cmdline").write_bytes(b"/usr/bin/python3\x00/opt/cloud/onedrive\x00--monitor\x00")

    class FakePath:
        def __init__(self, p):
            self.p = Path(p)

        def __call__(self, path_str):
            if str(path_str) == "/proc":
                return fake_proc
            return Path(path_str)

    assert check_process(
        "OneDrive.exe",
        _runner=mock_runner,
        _path_cls=FakePath(fake_proc),
    ) is True


def test_kill_process_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    mock_runner = MagicMock()
    mock_sleep = MagicMock()
    mock_checker = MagicMock(side_effect=[False])  # not running after kill

    res = kill_process(
        "OneDrive.exe",
        _runner=mock_runner,
        _sleep=mock_sleep,
        _checker=mock_checker,
    )
    assert res is True
    assert mock_runner.call_args[0][0] == ["taskkill", "/F", "/IM", "OneDrive.exe", "/T"]
    mock_sleep.assert_called_once()


def test_kill_process_win32_still_running(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    mock_runner = MagicMock()
    mock_sleep = MagicMock()
    mock_checker = MagicMock(return_value=True)  # still running

    res = kill_process(
        "OneDrive.exe",
        _runner=mock_runner,
        _sleep=mock_sleep,
        _checker=mock_checker,
    )
    assert res is False


def test_kill_process_posix(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    mock_runner = MagicMock()
    mock_sleep = MagicMock()
    mock_checker = MagicMock(return_value=False)

    res = kill_process(
        "Dropbox.exe",
        _runner=mock_runner,
        _sleep=mock_sleep,
        _checker=mock_checker,
    )
    assert res is True
    assert mock_runner.call_args[0][0][:2] == ["pkill", "-f"]


def test_launch_process_win32(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")

    exe1 = tmp_path / "app1.exe"
    exe2 = tmp_path / "app2.exe"
    exe2.write_text("dummy")

    calls = []

    def fake_popen(cmd):
        calls.append(cmd)

    res = launch_process(
        windows_candidates=[exe1, exe2],
        windows_args=["/background"],
        _popen=fake_popen,
    )
    assert res is True
    assert calls == [[str(exe2), "/background"]]


def test_launch_process_win32_none_found(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")

    exe = tmp_path / "missing.exe"
    res = launch_process(windows_candidates=[exe])
    assert res is False
    assert launch_process(windows_candidates=None) is False


def test_launch_process_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")

    calls = []

    def fake_popen(cmd):
        calls.append(cmd)

    res = launch_process(
        macos_app="Google Drive",
        macos_args=["--hide"],
        _popen=fake_popen,
    )
    assert res is True
    assert calls == [["open", "-a", "Google Drive", "--hide"]]

    assert launch_process(macos_app=None) is False


def test_launch_process_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    calls = []

    def fake_popen(cmd):
        calls.append(cmd)

    def fake_which(name):
        return f"/usr/bin/{name}" if name == "nextcloud" else None

    res = launch_process(
        linux_commands=[["missing-app"], ["nextcloud", "--background"]],
        _popen=fake_popen,
        _which=fake_which,
    )
    assert res is True
    assert calls == [["/usr/bin/nextcloud", "--background"]]

    assert launch_process(linux_commands=None) is False


def test_process_manager_facade(monkeypatch):
    mgr = ProcessManager()

    monkeypatch.setattr("cloudlockfixer.process.check_process", lambda exe: exe == "running.exe")
    monkeypatch.setattr("cloudlockfixer.process.kill_process", lambda exe, timeout=15.0: exe == "killable.exe")
    monkeypatch.setattr("cloudlockfixer.process.launch_process", lambda **kw: True)

    assert mgr.is_running("running.exe") is True
    assert mgr.is_running("stopped.exe") is False
    assert mgr.terminate("killable.exe") is True
    assert mgr.terminate("unkillable.exe") is False
    assert mgr.launch(macos_app="TestApp") is True
