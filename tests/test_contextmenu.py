"""Tests fuer contextmenu._command() — insbesondere PyInstaller-frozen-Erkennung."""
import sys
import types
import unittest.mock as mock

import pytest


def _get_command(op: str, frozen: bool, exe: str = r"C:\App\clf.exe"):
    """Importiert contextmenu mit simuliertem sys.frozen und sys.executable."""
    # Modul neu laden damit Patches wirken
    import importlib
    with mock.patch.object(sys, "frozen", frozen, create=True), \
         mock.patch.object(sys, "executable", exe):
        import cloudlockfixer.contextmenu as cm
        importlib.reload(cm)
        return cm._command(op)


def test_command_frozen_omits_script_path():
    """PyInstaller-Exe: kein pyw-Pfad, direkte Exe + subcommand."""
    exe = r"C:\App\CloudLockFixer.exe"
    cmd = _get_command("rename", frozen=True, exe=exe)
    assert exe in cmd
    assert ".pyw" not in cmd
    assert "gui-add" in cmd
    assert "--op rename" in cmd
    assert "--src" in cmd


def test_command_not_frozen_includes_launcher():
    """Quell-Installation: pythonw + clf_launcher.pyw als Argumente."""
    cmd = _get_command("move", frozen=False)
    assert ".pyw" in cmd or "launcher" in cmd.lower() or "clf_launcher" in cmd
    assert "gui-add" in cmd
    assert "--op move" in cmd


def test_command_frozen_format(tmp_path):
    """Befehl ist korrekt quotiert und enthält %1 als src-Platzhalter."""
    exe = str(tmp_path / "CloudLockFixer.exe")
    cmd = _get_command("delete", frozen=True, exe=exe)
    assert '"%1"' in cmd
    assert "--op delete" in cmd
    # Exe-Pfad muss gequotet sein (wegen möglicher Leerzeichen)
    assert f'"{exe}"' in cmd
