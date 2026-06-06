"""CloudLockFixer Tray-App (PySide6).

Startet mit Windows (Autostart), arbeitet die Queue beim Start + periodisch
(Default 2 h, einstellbar in 30-min-Schritten) + auf Knopfdruck ab. Worker laeuft
im Hintergrund-Thread, damit das Tray-Menue reaktiv bleibt.
"""
from __future__ import annotations

import logging
import os
import sys
import threading

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QInputDialog, QMenu, QMessageBox, QSystemTrayIcon,
)

from . import autostart, contextmenu, settings, watcher
from .i18n import t
from .models import Queue, Step, Task
from .paths import data_dir, log_file
from .providers import WATCHER_TICK_MS, available_providers, provider_for
from .worker import run_once

INTERVAL_CHOICES_MIN = [30, 60, 90, 120, 180, 240, 360, 720]


def _icon_paths() -> list[str]:
    out = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        out.append(os.path.join(base, "icon.ico"))
    here = os.path.dirname(os.path.abspath(__file__))
    out.append(os.path.join(here, "..", "..", "resources", "icon.ico"))
    return out


def _make_icon(color: str = "#2e9e44") -> QIcon:
    for cand in _icon_paths():
        if os.path.exists(cand):
            ic = QIcon(cand)
            if not ic.isNull():
                return ic
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(8, 26, 28, 26)
    p.drawEllipse(26, 18, 30, 28)
    p.drawRoundedRect(10, 38, 46, 16, 8, 8)
    p.setPen(QColor("white"))
    f = p.font()
    f.setBold(True)
    f.setPointSize(13)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "↻")
    p.end()
    return QIcon(pm)


class _Signals(QObject):
    done = Signal(dict)


class TrayApp:
    def __init__(self, app: QApplication):
        self.app = app
        self.queue = Queue(data_dir())
        self.settings = settings.load()
        self._running = False
        self.sig = _Signals()
        self.sig.done.connect(self._on_done)

        self.tray = QSystemTrayIcon(_make_icon())
        self.tray.setToolTip("CloudLockFixer")
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.run_async(False))
        self._apply_interval()

        self.providers = available_providers()
        self.watchers: dict[str, watcher.PreventiveWatcher] = {}
        watch_dirs = self.settings.get("watch_dirs", [])
        for prov in self.providers:
            dirs = [d for d in watch_dirs
                    if provider_for(d) is not None
                    and provider_for(d).name == prov.name]
            if dirs:
                self.watchers[prov.name] = watcher.PreventiveWatcher(
                    prov, watch_dirs=dirs)
        self._watch_running = False
        self.watch_timer = QTimer()
        self.watch_timer.timeout.connect(self._watcher_tick)
        if self.settings.get("watcher_enabled") and self.watchers:
            self.watch_timer.start(WATCHER_TICK_MS)

        self._refresh_status()
        QTimer.singleShot(3000, lambda: self.run_async(False))

    # ── Menü ────────────────────────────────────────────────────────
    def _build_menu(self) -> None:
        self.status_action = QAction("…")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.menu.addAction(QAction(t("add_task"), self.menu,
                                    triggered=self.add_task_dialog))
        self.menu.addAction(QAction(t("run_now"), self.menu,
                                    triggered=lambda: self.run_async(False)))
        self.menu.addAction(QAction(t("run_now_with_pause"), self.menu,
                                    triggered=lambda: self.run_async(True)))
        self.menu.addAction(QAction(t("open_queue_log"), self.menu,
                                    triggered=self._open_data_dir))

        interval_menu = self.menu.addMenu(t("interval_menu"))
        grp = QActionGroup(self.menu)
        grp.setExclusive(True)
        cur = int(self.settings.get("interval_min", settings.DEFAULT_INTERVAL_MIN))
        for m in INTERVAL_CHOICES_MIN:
            label = f"{m} min" if m < 60 else (f"{m // 60} h" if m % 60 == 0
                                               else f"{m / 60:.1f} h")
            a = QAction(label, self.menu, checkable=True)
            a.setChecked(m == cur)
            a.triggered.connect(lambda _=False, mm=m: self._set_interval(mm))
            grp.addAction(a)
            interval_menu.addAction(a)

        self.autostart_action = QAction(t("autostart_label"), self.menu,
                                        checkable=True)
        self.autostart_action.setChecked(autostart.is_enabled())
        self.autostart_action.triggered.connect(self._toggle_autostart)
        self.menu.addAction(self.autostart_action)

        self.context_action = QAction(t("context_menu_label"), self.menu,
                                      checkable=True)
        self.context_action.setChecked(contextmenu.is_installed())
        self.context_action.triggered.connect(self._toggle_context)
        self.menu.addAction(self.context_action)

        self.watcher_action = QAction(t("watcher_label"), self.menu,
                                      checkable=True)
        self.watcher_action.setChecked(bool(self.settings.get("watcher_enabled")))
        self.watcher_action.triggered.connect(self._toggle_watcher)
        self.menu.addAction(self.watcher_action)
        self.menu.addAction(QAction(t("add_watch_dir"), self.menu,
                                    triggered=self._add_watch_dir))

        # Sprache / Language
        lang_menu = self.menu.addMenu(t("language_menu"))
        lang_grp = QActionGroup(self.menu)
        lang_grp.setExclusive(True)
        cur_lang = self.settings.get("language", "auto")
        for code, label in [("auto", t("language_auto")),
                            ("de", "Deutsch"), ("en", "English")]:
            a = QAction(label, self.menu, checkable=True)
            a.setChecked(code == cur_lang)
            a.triggered.connect(lambda _=False, c=code: self._set_language(c))
            lang_grp.addAction(a)
            lang_menu.addAction(a)

        self.menu.addSeparator()
        self.menu.addAction(QAction(t("quit_label"), self.menu,
                                    triggered=self.app.quit))

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.menu.popup(self.tray.geometry().center())

    # ── Aktionen ────────────────────────────────────────────────────
    def add_task_dialog(self) -> None:
        action, ok = QInputDialog.getItem(
            None, "CloudLockFixer", t("action_choose"),
            [t("action_rename"), t("action_move"), t("action_delete")], 0, False)
        if not ok:
            return
        src = QFileDialog.getExistingDirectory(None, t("choose_folder"))
        if not src:
            return
        if action == t("action_rename"):
            new, ok = QInputDialog.getText(None, t("action_rename"),
                                           t("rename_prompt"))
            if not ok or not new.strip():
                return
            task = Task(chain=[Step(op="rename", src=src, arg=new.strip())])
        elif action == t("action_move"):
            dst_parent = QFileDialog.getExistingDirectory(None, t("choose_target"))
            if not dst_parent:
                return
            name = os.path.basename(src.rstrip("/\\"))
            task = Task(chain=[Step(op="move", src=src,
                                    arg=os.path.join(dst_parent, name))])
        else:
            if QMessageBox.question(
                    None, t("confirm_delete_title"),
                    t("confirm_delete", src=src)
            ) != QMessageBox.StandardButton.Yes:
                return
            task = Task(chain=[Step(op="delete", src=src)])
        self.queue.add(task)
        self._refresh_status()
        self.tray.showMessage("CloudLockFixer",
                              t("queued_notification", desc=task.describe()),
                              _make_icon(), 4000)

    def run_async(self, force_pause: bool) -> None:
        if self._running:
            return
        self._running = True
        self._set_status(t("status_running"))

        def job():
            try:
                s = run_once(self.queue, force_pause=force_pause)
            except Exception as e:  # pragma: no cover
                s = {"error": str(e)}
            self.sig.done.emit(s)

        threading.Thread(target=job, daemon=True).start()

    def _on_done(self, s: dict) -> None:
        self._running = False
        self._refresh_status()
        if s.get("done"):
            self.tray.showMessage("CloudLockFixer",
                                  t("actions_done", n=s["done"]),
                                  _make_icon(), 4000)

    def _toggle_autostart(self, checked: bool) -> None:
        ok = autostart.enable() if checked else autostart.disable()
        if not ok:
            self.autostart_action.setChecked(autostart.is_enabled())

    def _set_interval(self, minutes: int) -> None:
        self.settings["interval_min"] = minutes
        settings.save(self.settings)
        self._apply_interval()

    def _apply_interval(self) -> None:
        minutes = int(self.settings.get("interval_min", settings.DEFAULT_INTERVAL_MIN))
        self.timer.start(minutes * 60 * 1000)

    def _open_data_dir(self) -> None:
        try:
            os.startfile(str(data_dir()))  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            pass

    def _set_language(self, code: str) -> None:
        self.settings["language"] = code
        settings.save(self.settings)
        self.tray.showMessage("CloudLockFixer", t("restart_required"),
                              _make_icon(), 4000)

    # ── Status ──────────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self.status_action.setText(text)
        self.tray.setToolTip(f"CloudLockFixer — {text}")

    def _refresh_status(self) -> None:
        self.queue.load()
        n = len(self.queue.pending)
        failed = sum(1 for t_ in self.queue.tasks
                     if t_.status == "pending" and t_.retry_count > 0)
        txt = (t("status_no_tasks") if n == 0
               else t("status_open", n=n, failed=failed))
        self._set_status(txt)

    # ── P2: Kontextmenü ─────────────────────────────────────────────
    def _toggle_context(self, checked: bool) -> None:
        ok = contextmenu.install() if checked else contextmenu.uninstall()
        if not ok:
            self.context_action.setChecked(contextmenu.is_installed())

    # ── P3: Präventiv-Wächter ───────────────────────────────────────
    def _toggle_watcher(self, checked: bool) -> None:
        self.settings["watcher_enabled"] = checked
        settings.save(self.settings)
        if checked and self.watchers:
            self.watch_timer.start(WATCHER_TICK_MS)
        else:
            self.watch_timer.stop()

    def _add_watch_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(None, t("watcher_dir_title"))
        if not d:
            return
        dirs = self.settings.get("watch_dirs", [])
        if d not in dirs:
            dirs.append(d)
            self.settings["watch_dirs"] = dirs
            settings.save(self.settings)
            prov = provider_for(d)
            if prov and prov.name in self.watchers:
                self.watchers[prov.name].watch_dirs.append(d)
            elif prov:
                self.watchers[prov.name] = watcher.PreventiveWatcher(
                    prov, watch_dirs=[d])
        if (self.settings.get("watcher_enabled")
                and not self.watch_timer.isActive()):
            self.watch_timer.start(WATCHER_TICK_MS)
        self.tray.showMessage("CloudLockFixer", t("watch_dir_added", d=d),
                              _make_icon(), 3000)

    def _watcher_tick(self) -> None:
        if self._watch_running:
            return
        self._watch_running = True

        def job():
            try:
                watcher.tick_all(self.watchers)
            except Exception:  # pragma: no cover
                pass
            self._watch_running = False

        threading.Thread(target=job, daemon=True).start()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file(), encoding="utf-8")],
    )

    # Language must be resolved before any UI strings are used
    from . import i18n
    cfg = settings.load()
    i18n.set_language(settings.resolve_language(cfg))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from PySide6.QtCore import QSharedMemory
    guard = QSharedMemory("CloudLockFixer_singleton")
    if not guard.create(1):
        QMessageBox.information(None, "CloudLockFixer", t("already_running"))
        return 0
    app._clf_guard = guard

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "CloudLockFixer", t("no_tray"))
        return 1

    TrayApp(app)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
