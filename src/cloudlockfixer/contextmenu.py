"""Desktop context menu integration for Windows (HKCU registry), Linux (Nautilus scripts / KDE ServiceMenus), and macOS (Services / Quick Actions).

Right-click entries invoke `clf gui-add --op <op> --src <path>`.
"""
from __future__ import annotations

import os
import plistlib
import shutil
import sys
from pathlib import Path

from . import paths
from .i18n import t

_BASES = [
    r"Software\Classes\Directory\shell\CloudLockFixer",
    r"Software\Classes\*\shell\CloudLockFixer",
]
_OPS = [
    ("01rename", "ctx_delayed_rename", "rename"),
    ("02move", "ctx_delayed_move", "move"),
    ("03delete", "ctx_delayed_delete", "delete"),
]


def _launch_args() -> tuple[str, ...]:
    if getattr(sys, "frozen", False):
        return (sys.executable,)
    return (paths.pythonw(), str(paths.launcher()))


def _command(op: str) -> str:
    """Windows Explorer command string calling gui-add."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" gui-add --op {op} --src "%1"'
    return f'"{paths.pythonw()}" "{paths.launcher()}" gui-add --op {op} --src "%1"'


def _quote_sh(value: str) -> str:
    """Quote one argument for POSIX shell and desktop execution."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace(chr(96), "\\" + chr(96))
        .replace("$", "\\$")
        .replace("%", "%%")
    )
    return f'"{escaped}"'


def _desktop_exec_command() -> str:
    return " ".join(_quote_sh(arg) for arg in _launch_args())


# ---------------------------------------------------------------------------
# Windows HKCU Registry Implementation
# ---------------------------------------------------------------------------

def _win_is_installed() -> bool:
    import winreg

    for base in _BASES:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base):
                return True
        except OSError:
            continue
    return False


def _win_install() -> bool:
    import winreg

    try:
        for base in _BASES:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base) as k:
                winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "CloudLockFixer")
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


def _win_uninstall() -> bool:
    import winreg

    for base in _BASES:
        _delete_tree(winreg.HKEY_CURRENT_USER, base)
    return not _win_is_installed()


# ---------------------------------------------------------------------------
# Linux Implementation (Nautilus Scripts & KDE/Dolphin ServiceMenus)
# ---------------------------------------------------------------------------

def _linux_nautilus_dir() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return base / "nautilus" / "scripts" / "CloudLockFixer"


def _linux_kio_dir() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return base / "kio" / "servicemenus"


def _linux_nautilus_script_content(op: str, label_key: str) -> str:
    cmd = _desktop_exec_command()
    return (
        "#!/bin/sh\n"
        f"# CloudLockFixer - {t(label_key)}\n"
        "CMD=" + cmd + "\n"
        "if [ -n \"$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS\" ]; then\n"
        "    printf '%s\\n' \"$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS\" | while IFS= read -r f || [ -n \"$f\" ]; do\n"
        f"        [ -n \"$f\" ] && $CMD gui-add --op {op} --src \"$f\"\n"
        "    done\n"
        "elif [ -n \"$1\" ]; then\n"
        "    for f in \"$@\"; do\n"
        f"        $CMD gui-add --op {op} --src \"$f\"\n"
        "    done\n"
        "fi\n"
    )


def _linux_kio_desktop_content() -> str:
    cmd = _desktop_exec_command()
    return (
        "[Desktop Entry]\n"
        "Type=Service\n"
        "ServiceTypes=KonqPopupMenu/Plugin\n"
        "MimeType=all/all;all/allfiles;inode/directory;\n"
        "Actions=rename;move;delete;\n"
        "X-KDE-Submenu=CloudLockFixer\n"
        "\n"
        "[Desktop Action rename]\n"
        f"Name={t('ctx_delayed_rename')}\n"
        f"Exec={cmd} gui-add --op rename --src %f\n"
        "\n"
        "[Desktop Action move]\n"
        f"Name={t('ctx_delayed_move')}\n"
        f"Exec={cmd} gui-add --op move --src %f\n"
        "\n"
        "[Desktop Action delete]\n"
        f"Name={t('ctx_delayed_delete')}\n"
        f"Exec={cmd} gui-add --op delete --src %f\n"
    )


def _linux_is_installed() -> bool:
    nautilus_dir = _linux_nautilus_dir()
    nautilus_ok = (
        nautilus_dir.is_dir()
        and (nautilus_dir / "01_delayed_rename.sh").exists()
        and (nautilus_dir / "02_delayed_move.sh").exists()
        and (nautilus_dir / "03_delayed_delete.sh").exists()
    )
    kio_desktop = _linux_kio_dir() / "cloudlockfixer.desktop"
    kio_ok = kio_desktop.is_file()
    return nautilus_ok or kio_ok


def _linux_install() -> bool:
    try:
        nautilus_dir = _linux_nautilus_dir()
        nautilus_dir.mkdir(parents=True, exist_ok=True)
        scripts = [
            ("01_delayed_rename.sh", "rename", "ctx_delayed_rename"),
            ("02_delayed_move.sh", "move", "ctx_delayed_move"),
            ("03_delayed_delete.sh", "delete", "ctx_delayed_delete"),
        ]
        for name, op, label_key in scripts:
            target = nautilus_dir / name
            target.write_text(_linux_nautilus_script_content(op, label_key), encoding="utf-8", newline="\n")
            target.chmod(0o755)

        kio_dir = _linux_kio_dir()
        kio_dir.mkdir(parents=True, exist_ok=True)
        (kio_dir / "cloudlockfixer.desktop").write_text(_linux_kio_desktop_content(), encoding="utf-8", newline="\n")
        return True
    except OSError:
        return False


def _linux_uninstall() -> bool:
    nautilus_dir = _linux_nautilus_dir()
    if nautilus_dir.exists():
        shutil.rmtree(nautilus_dir, ignore_errors=True)

    kio_file = _linux_kio_dir() / "cloudlockfixer.desktop"
    if kio_file.exists():
        try:
            kio_file.unlink(missing_ok=True)
        except OSError:
            pass

    return not _linux_is_installed()


# ---------------------------------------------------------------------------
# macOS Implementation (Services / Automator Quick Actions)
# ---------------------------------------------------------------------------

_MACOS_SERVICES = [
    ("CloudLockFixer - Delayed Rename.workflow", "rename", "ctx_delayed_rename"),
    ("CloudLockFixer - Delayed Move.workflow", "move", "ctx_delayed_move"),
    ("CloudLockFixer - Delayed Delete.workflow", "delete", "ctx_delayed_delete"),
]


def _macos_services_dir() -> Path:
    return Path.home() / "Library" / "Services"


def _macos_is_installed() -> bool:
    services_dir = _macos_services_dir()
    for name, _, _ in _MACOS_SERVICES:
        info_plist = services_dir / name / "Contents" / "Info.plist"
        if not info_plist.is_file():
            return False
    return True


def _macos_install() -> bool:
    services_dir = _macos_services_dir()
    cmd = _desktop_exec_command()

    try:
        services_dir.mkdir(parents=True, exist_ok=True)
        for name, op, label_key in _MACOS_SERVICES:
            wf_dir = services_dir / name / "Contents"
            wf_dir.mkdir(parents=True, exist_ok=True)

            title = t(label_key)
            info_payload = {
                "CFBundleIdentifier": f"com.cloudlockfixer.service.{op}",
                "CFBundleName": f"CloudLockFixer - {title}",
                "CFBundleVersion": "1.0",
                "NSServices": [
                    {
                        "NSMenuItem": {
                            "default": f"CloudLockFixer: {title}",
                        },
                        "NSMessage": "runWorkflowAsService",
                        "NSSendFileTypes": ["public.item"],
                    }
                ],
            }
            with (wf_dir / "Info.plist").open("wb") as f:
                plistlib.dump(info_payload, f, fmt=plistlib.FMT_XML)

            workflow_payload = {
                "AMApplicationBuild": "523",
                "AMApplicationVersion": "2.10",
                "AMDocumentVersion": "2",
                "actions": [
                    {
                        "action": {
                            "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                            "ActionName": "Run Shell Script",
                            "ActionParameters": {
                                "COMMAND_STRING": (
                                    'for f in "$@"; do\n'
                                    f'  {cmd} gui-add --op {op} --src "$f"\n'
                                    "done\n"
                                ),
                                "inputMethod": 1,
                                "shell": "/bin/zsh",
                            },
                            "BundleIdentifier": "com.apple.RunShellScript",
                        }
                    }
                ],
                "workflowMetaData": {
                    "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
                },
            }
            with (wf_dir / "document.wflow").open("wb") as f:
                plistlib.dump(workflow_payload, f, fmt=plistlib.FMT_XML)

        return True
    except OSError:
        return False


def _macos_uninstall() -> bool:
    services_dir = _macos_services_dir()
    for name, _, _ in _MACOS_SERVICES:
        wf_dir = services_dir / name
        if wf_dir.exists():
            shutil.rmtree(wf_dir, ignore_errors=True)

    return not _macos_is_installed()


# ---------------------------------------------------------------------------
# Public Platform Dispatchers
# ---------------------------------------------------------------------------

def is_installed() -> bool:
    """Returns True if context menu integration is installed on current OS."""
    if sys.platform == "win32":
        return _win_is_installed()
    if sys.platform.startswith("linux"):
        return _linux_is_installed()
    if sys.platform == "darwin":
        return _macos_is_installed()
    return False


def install() -> bool:
    """Installs context menu integration for current OS."""
    if sys.platform == "win32":
        return _win_install()
    if sys.platform.startswith("linux"):
        return _linux_install()
    if sys.platform == "darwin":
        return _macos_install()
    return False


def uninstall() -> bool:
    """Uninstalls context menu integration for current OS."""
    if sys.platform == "win32":
        return _win_uninstall()
    if sys.platform.startswith("linux"):
        return _linux_uninstall()
    if sys.platform == "darwin":
        return _macos_uninstall()
    return False
