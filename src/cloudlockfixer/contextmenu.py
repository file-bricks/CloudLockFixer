"""Explorer-Rechtsklick-Kontextmenue (Windows, HKCU) als Kaskaden-Untermenue
'CloudLockFixer' fuer Ordner und Dateien. Eintraege rufen `clf gui-add`."""
from __future__ import annotations

import sys

from .i18n import t
from .paths import launcher, pythonw

_BASES = [
    r"Software\Classes\Directory\shell\CloudLockFixer",
    r"Software\Classes\*\shell\CloudLockFixer",
]
_OPS = [
    ("01rename", "ctx_delayed_rename", "rename"),
    ("02move", "ctx_delayed_move", "move"),
    ("03delete", "ctx_delayed_delete", "delete"),
]


def _command(op: str) -> str:
    return f'"{pythonw()}" "{launcher()}" gui-add --op {op} --src "%1"'


def is_installed() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    for base in _BASES:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base):
                return True
        except OSError:
            continue
    return False


def install() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        for base in _BASES:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base) as k:
                winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "CloudLockFixer")
                # leerer SubCommands-Wert aktiviert die shell-Unterverben
                winreg.SetValueEx(k, "subcommands", 0, winreg.REG_SZ, "")
            for key, label_key, op in _OPS:
                vk = base + "\\shell\\" + key
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, vk) as k:
                    winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, t(label_key))
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, vk + r"\command") as k:
                    winreg.SetValueEx(k, None, 0, winreg.REG_SZ, _command(op))
        return True
    except OSError:
        return False


def _delete_tree(root, path: str) -> None:
    import winreg
    try:
        with winreg.OpenKey(root, path) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _delete_tree(root, path + "\\" + sub)
        winreg.DeleteKey(root, path)
    except OSError:
        pass


def uninstall() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    for base in _BASES:
        _delete_tree(winreg.HKEY_CURRENT_USER, base)
    return not is_installed()
