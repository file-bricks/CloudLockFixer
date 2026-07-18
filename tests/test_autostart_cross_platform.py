"""Cross-platform autostart contracts for CloudLockFixer."""
from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

import cloudlockfixer.autostart as autostart
import cloudlockfixer.paths as paths


def _configure_linux(
    monkeypatch,
    tmp_path: Path,
    *,
    executable: str = "/opt/Python 3/bin/python3",
    launcher: str = "/home/test/Cloud Lock/clf_launcher.pyw",
) -> Path:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg config"))
    monkeypatch.setattr(paths, "pythonw", lambda: executable)
    monkeypatch.setattr(paths, "launcher", lambda: PurePosixPath(launcher))
    return tmp_path / "xdg config" / "autostart" / "cloudlockfixer.desktop"


def test_linux_xdg_autostart_roundtrip(monkeypatch, tmp_path):
    desktop_file = _configure_linux(monkeypatch, tmp_path)

    assert not autostart.is_enabled()
    assert autostart.enable()

    content = desktop_file.read_text(encoding="utf-8")
    assert content.startswith("[Desktop Entry]\n")
    assert "Type=Application\n" in content
    assert "Name=CloudLockFixer\n" in content
    assert (
        'Exec="/opt/Python 3/bin/python3" '
        '"/home/test/Cloud Lock/clf_launcher.pyw"\n'
    ) in content
    assert "Terminal=false\n" in content
    assert "Hidden=false\n" in content
    assert "X-GNOME-Autostart-enabled=true\n" in content
    assert autostart.is_enabled()

    assert autostart.disable()
    assert not desktop_file.exists()
    assert autostart.disable()


def test_linux_autostart_rejects_stale_desktop_entry(monkeypatch, tmp_path):
    desktop_file = _configure_linux(monkeypatch, tmp_path)
    desktop_file.parent.mkdir(parents=True)
    desktop_file.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=CloudLockFixer\n"
        "Exec=/tmp/old-cloudlockfixer\n"
        "Terminal=false\n"
        "Hidden=false\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8",
    )

    assert not autostart.is_enabled()
    assert autostart.enable()
    assert autostart.is_enabled()
    assert "/tmp/old-cloudlockfixer" not in desktop_file.read_text(encoding="utf-8")


def test_linux_autostart_escapes_desktop_exec_metacharacters(monkeypatch, tmp_path):
    desktop_file = _configure_linux(
        monkeypatch,
        tmp_path,
        executable="/opt/py$thon/bin/py%thon3",
        launcher='/home/test/Cloud "Lock"/clf_launcher.pyw',
    )

    assert autostart.enable()
    content = desktop_file.read_text(encoding="utf-8")
    assert (
        'Exec="/opt/py\\$thon/bin/py%%thon3" '
        '"/home/test/Cloud \\"Lock\\"/clf_launcher.pyw"\n'
    ) in content


def test_macos_autostart_remains_explicitly_unsupported(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")

    assert not autostart.is_enabled()
    assert not autostart.enable()
    assert not autostart.disable()
