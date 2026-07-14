from pathlib import Path

import cloudlockfixer.paths as paths


def test_data_dir_uses_localappdata_on_windows(monkeypatch, tmp_path):
    local = tmp_path / "LocalAppData"
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local))

    result = paths.data_dir()

    assert result == local / "CloudLockFixer"
    assert result.exists()


def test_data_dir_windows_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = paths.data_dir()

    assert result == tmp_path / ".cloudlockfixer"
    assert result.exists()


def test_data_dir_uses_macos_application_support(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    result = paths.data_dir()

    assert result == tmp_path / "Library" / "Application Support" / "CloudLockFixer"
    assert result.exists()


def test_data_dir_uses_xdg_data_home_on_linux(monkeypatch, tmp_path):
    xdg = tmp_path / "xdg-data"
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    result = paths.data_dir()

    assert result == xdg / "cloudlockfixer"
    assert result.exists()


def test_data_dir_linux_falls_back_to_local_share(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = paths.data_dir()

    assert result == tmp_path / ".local" / "share" / "cloudlockfixer"
    assert result.exists()
