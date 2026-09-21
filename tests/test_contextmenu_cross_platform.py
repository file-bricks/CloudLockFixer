"""Cross-platform context menu contracts for CloudLockFixer."""
from __future__ import annotations

import plistlib
import sys
from pathlib import Path, PurePosixPath
import unittest.mock as mock

import cloudlockfixer.contextmenu as contextmenu
import cloudlockfixer.paths as paths


def _configure_linux(
    monkeypatch,
    tmp_path: Path,
    *,
    executable: str = "/usr/bin/python3",
    launcher: str = "/home/test/Cloud Lock/clf_launcher.pyw",
) -> tuple[Path, Path]:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg_data"))
    monkeypatch.setattr(paths, "pythonw", lambda: executable)
    monkeypatch.setattr(paths, "launcher", lambda: PurePosixPath(launcher))
    nautilus_dir = tmp_path / "xdg_data" / "nautilus" / "scripts" / "CloudLockFixer"
    kio_desktop = tmp_path / "xdg_data" / "kio" / "servicemenus" / "cloudlockfixer.desktop"
    return nautilus_dir, kio_desktop


def test_linux_contextmenu_install_roundtrip(monkeypatch, tmp_path):
    nautilus_dir, kio_desktop = _configure_linux(monkeypatch, tmp_path)

    assert not contextmenu.is_installed()
    assert contextmenu.install()
    assert contextmenu.is_installed()

    # Check Nautilus scripts
    assert nautilus_dir.is_dir()
    for script_name, expected_op in [
        ("01_delayed_rename.sh", "rename"),
        ("02_delayed_move.sh", "move"),
        ("03_delayed_delete.sh", "delete"),
    ]:
        script = nautilus_dir / script_name
        assert script.is_file()
        content = script.read_text(encoding="utf-8")
        assert content.startswith("#!/bin/sh\n")
        assert f"--op {expected_op}" in content
        assert "NAUTILUS_SCRIPT_SELECTED_FILE_PATHS" in content
        assert "/home/test/Cloud Lock/clf_launcher.pyw" in content

    # Check KDE ServiceMenu desktop file
    assert kio_desktop.is_file()
    desktop_content = kio_desktop.read_text(encoding="utf-8")
    assert "[Desktop Entry]\n" in desktop_content
    assert "Type=Service\n" in desktop_content
    assert "Actions=rename;move;delete;\n" in desktop_content
    assert "[Desktop Action rename]\n" in desktop_content
    assert "[Desktop Action move]\n" in desktop_content
    assert "[Desktop Action delete]\n" in desktop_content
    assert "--op rename --src %f" in desktop_content
    assert "--op move --src %f" in desktop_content
    assert "--op delete --src %f" in desktop_content

    # Uninstall
    assert contextmenu.uninstall()
    assert not contextmenu.is_installed()
    assert not nautilus_dir.exists()
    assert not kio_desktop.exists()
    # Idempotent
    assert contextmenu.uninstall()


def test_linux_contextmenu_frozen_executable(monkeypatch, tmp_path):
    nautilus_dir, kio_desktop = _configure_linux(
        monkeypatch, tmp_path, executable="/opt/CloudLockFixer/clf"
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert contextmenu.install()
    script = (nautilus_dir / "01_delayed_rename.sh").read_text(encoding="utf-8")
    assert 'CMD="/opt/CloudLockFixer/clf"' in script

    desktop = kio_desktop.read_text(encoding="utf-8")
    assert 'Exec="/opt/CloudLockFixer/clf" gui-add --op rename --src %f' in desktop


def _configure_macos(
    monkeypatch,
    tmp_path: Path,
    *,
    executable: str = "/usr/bin/python3",
    launcher: str = "/Users/test/Cloud Lock/clf_launcher.pyw",
) -> Path:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(paths, "pythonw", lambda: executable)
    monkeypatch.setattr(paths, "launcher", lambda: PurePosixPath(launcher))
    return tmp_path / "Library" / "Services"


def test_macos_contextmenu_install_roundtrip(monkeypatch, tmp_path):
    services_dir = _configure_macos(monkeypatch, tmp_path)

    assert not contextmenu.is_installed()
    assert contextmenu.install()
    assert contextmenu.is_installed()

    for name, op in [
        ("CloudLockFixer - Delayed Rename.workflow", "rename"),
        ("CloudLockFixer - Delayed Move.workflow", "move"),
        ("CloudLockFixer - Delayed Delete.workflow", "delete"),
    ]:
        wf_dir = services_dir / name / "Contents"
        assert wf_dir.is_dir()

        info_plist = wf_dir / "Info.plist"
        assert info_plist.is_file()
        with info_plist.open("rb") as f:
            info = plistlib.load(f)
        assert info["CFBundleIdentifier"] == f"com.cloudlockfixer.service.{op}"
        assert info["NSServices"][0]["NSMessage"] == "runWorkflowAsService"
        assert info["NSServices"][0]["NSSendFileTypes"] == ["public.item"]

        wflow = wf_dir / "document.wflow"
        assert wflow.is_file()
        with wflow.open("rb") as f:
            wf = plistlib.load(f)
        assert wf["workflowMetaData"]["workflowTypeIdentifier"] == "com.apple.Automator.servicesMenu"
        cmd = wf["actions"][0]["action"]["ActionParameters"]["COMMAND_STRING"]
        assert f"--op {op}" in cmd
        assert "/Users/test/Cloud Lock/clf_launcher.pyw" in cmd

    # Uninstall
    assert contextmenu.uninstall()
    assert not contextmenu.is_installed()
    assert not (services_dir / "CloudLockFixer - Delayed Rename.workflow").exists()
    assert contextmenu.uninstall()


def test_unsupported_platform_returns_false(monkeypatch):
    monkeypatch.setattr(sys, "platform", "freebsd")
    assert not contextmenu.is_installed()
    assert not contextmenu.install()
    assert not contextmenu.uninstall()


def test_windows_registry_mocked_install_and_uninstall(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    created_keys = set()
    values = {}

    class MockKey:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    mock_winreg = mock.MagicMock()
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.REG_SZ = 1

    def mock_create_key(root, subkey):
        created_keys.add(subkey)
        return MockKey(subkey)

    def mock_set_value_ex(key, name, reserved, dtype, value):
        values[(key.name, name)] = value

    def mock_open_key(root, subkey):
        if subkey in created_keys:
            return MockKey(subkey)
        raise OSError("Key not found")

    mock_winreg.CreateKey = mock_create_key
    mock_winreg.SetValueEx = mock_set_value_ex
    mock_winreg.OpenKey = mock_open_key
    mock_winreg.EnumKey = mock.MagicMock(side_effect=OSError("End of enum"))
    mock_winreg.DeleteKey = lambda root, path: created_keys.discard(path)

    monkeypatch.setitem(sys.modules, "winreg", mock_winreg)

    assert contextmenu.install()
    assert contextmenu.is_installed()
    assert ("Software\\Classes\\Directory\\shell\\CloudLockFixer", "MUIVerb") in values
    assert ("Software\\Classes\\*\\shell\\CloudLockFixer", "MUIVerb") in values

    assert contextmenu.uninstall()
    assert not contextmenu.is_installed()
