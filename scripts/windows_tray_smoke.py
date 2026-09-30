"""Native Windows source smoke using a private queue and singleton key.

Run with PYTHONPATH=src. Registry integrations are only read; providers are
replaced with doubles. This is not a login, manual usability, or release test.
Evidence (receipt and rendered menu) stays in a new local temporary directory.
"""
from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import sys
import tempfile
import winreg

from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QSystemTrayIcon

from cloudlockfixer import autostart, contextmenu, i18n, tray, worker
from cloudlockfixer.models import Queue, Step, Task


def registry_snapshot() -> dict:
    result = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, autostart._RUN_KEY) as key:
            result["autostart"] = winreg.QueryValueEx(key, autostart._VALUE)
    except FileNotFoundError:
        result["autostart"] = None

    def visit(path):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                children, values, _ = winreg.QueryInfoKey(key)
                result[path] = [winreg.EnumValue(key, i) for i in range(values)]
                for index in range(children):
                    visit(path + "\\" + winreg.EnumKey(key, index))
        except FileNotFoundError:
            result[path] = None

    for base in contextmenu._BASES:
        visit(base)
    return result


def main() -> int:
    if sys.platform != "win32":
        raise RuntimeError("This smoke requires a native Windows desktop")
    if os.environ.get("QT_QPA_PLATFORM", "windows") != "windows":
        raise RuntimeError("Offscreen Qt cannot establish native tray evidence")
    root = Path(tempfile.mkdtemp(prefix="clf-native-tray-"))
    os.environ["LOCALAPPDATA"] = str(root / "profile")
    before = registry_snapshot()
    queue = Queue(root / "profile" / "CloudLockFixer")
    for name in ("rename", "move", "delete"):
        source = root / (name + ".txt")
        source.write_text(name + " payload", encoding="utf-8")
        argument = "renamed.txt" if name == "rename" else str(root / "moved.txt")
        queue.add(Task(id=name, chain=[Step(op=name, src=str(source), arg=argument)]))

    def forbidden(*args, **kwargs):
        raise AssertionError("Smoke attempted to change desktop integration")

    autostart.enable = autostart.disable = forbidden
    contextmenu.install = contextmenu.uninstall = forbidden
    tray.available_providers = lambda: []
    tray.provider_for = worker.provider_for = lambda path: None
    original_guard = QtCore.QSharedMemory

    class IsolatedGuard(original_guard):
        def __init__(self, key):
            super().__init__(key + "-smoke-" + str(os.getpid()))

    QtCore.QSharedMemory = IsolatedGuard
    original_tray = tray.TrayApp
    receipt = {"scope": "native-source-with-provider-doubles", "temp_root": str(root)}
    failures = []

    def capture(app):
        instance = original_tray(app)

        def inspect():
            try:
                gc.collect()
                assert QSystemTrayIcon.isSystemTrayAvailable()
                assert instance.tray.isVisible()
                assert not instance._running
                labels = [action.text() for action in instance.menu.actions()]
                for key in ("add_task", "run_now", "open_data_folder", "interval_menu",
                            "autostart_label", "context_menu_label", "watcher_label",
                            "language_menu", "quit_label"):
                    assert i18n.t(key) in labels, key
                assert all(task.status == "done" for task in instance.queue.tasks)
                assert len(instance.queue.tasks) == 3
                assert (root / "renamed.txt").read_text(encoding="utf-8") == "rename payload"
                assert (root / "moved.txt").read_text(encoding="utf-8") == "move payload"
                for name in ("rename", "move", "delete"):
                    assert not (root / (name + ".txt")).exists()
                assert registry_snapshot() == before
                instance.menu.ensurePolished()
                instance.menu.adjustSize()
                assert instance.menu.grab().save(str(root / "menu.png"))
                receipt.update(menu_labels=labels, registry_unchanged=True,
                               tray_visible=True, temp_operations="rename/move/delete passed",
                               autostart_read=instance.autostart_action.isChecked(),
                               contextmenu_read=instance.context_action.isChecked())
                quit_action = next(a for a in instance.menu.actions() if a.text() == i18n.t("quit_label"))
                quit_action.trigger()
            except Exception as error:
                failures.append(repr(error))
                app.quit()
            finally:
                instance.tray.hide()

        QTimer.singleShot(6000, inspect)
        return instance

    tray.TrayApp = capture
    exit_code = tray.main()
    assert registry_snapshot() == before
    receipt.update(exit_code=exit_code, failures=failures)
    (root / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 1 if failures or exit_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
