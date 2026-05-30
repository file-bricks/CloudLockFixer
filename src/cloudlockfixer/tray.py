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
from .models import Queue, Step, Task
from .paths import data_dir, log_file
from .providers import OneDriveProvider
from .worker import run_once

INTERVAL_CHOICES_MIN = [30, 60, 90, 120, 180, 240, 360, 720]


def _icon_paths() -> list[str]:
    """Mögliche Orte der icon.ico (gebündelt in der EXE bzw. im Projekt)."""
    out = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        out.append(os.path.join(base, "icon.ico"))
    here = os.path.dirname(os.path.abspath(__file__))
    out.append(os.path.join(here, "..", "..", "resources", "icon.ico"))
    return out


def _make_icon(color: str = "#2e9e44") -> QIcon:
    """App-Icon: bevorzugt die icon.ico (grüne Wolke + Schloss); fällt sonst
    auf ein programmatisch gezeichnetes Wolken-Icon zurück."""
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
    # einfache Wolke aus drei Ellipsen + Basis
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

        # Praeventiv-Waechter (opt-in)
        self.watcher = watcher.PreventiveWatcher(
            OneDriveProvider(), watch_dirs=self.settings.get("watch_dirs", []))
        self._watch_running = False
        self.watch_timer = QTimer()
        self.watch_timer.timeout.connect(self._watcher_tick)
        if self.settings.get("watcher_enabled"):
            self.watch_timer.start(int(self.watcher.window_s * 1000))

        self._refresh_status()
        QTimer.singleShot(3000, lambda: self.run_async(False))  # kurz nach Start

    # ── Menü ────────────────────────────────────────────────────────
    def _build_menu(self) -> None:
        self.status_action = QAction("…")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.menu.addAction(QAction("Task hinzufügen…", self.menu,
                                    triggered=self.add_task_dialog))
        self.menu.addAction(QAction("Jetzt ausführen", self.menu,
                                    triggered=lambda: self.run_async(False)))
        self.menu.addAction(QAction("Jetzt ausführen (mit OneDrive-Pause)", self.menu,
                                    triggered=lambda: self.run_async(True)))
        self.menu.addAction(QAction("Queue/Log öffnen", self.menu,
                                    triggered=self._open_data_dir))

        interval_menu = self.menu.addMenu("Intervall")
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

        self.autostart_action = QAction("Mit Windows starten", self.menu,
                                        checkable=True)
        self.autostart_action.setChecked(autostart.is_enabled())
        self.autostart_action.triggered.connect(self._toggle_autostart)
        self.menu.addAction(self.autostart_action)

        self.context_action = QAction("Explorer-Kontextmenü", self.menu,
                                      checkable=True)
        self.context_action.setChecked(contextmenu.is_installed())
        self.context_action.triggered.connect(self._toggle_context)
        self.menu.addAction(self.context_action)

        self.watcher_action = QAction("Präventiv-Wächter (OneDrive)", self.menu,
                                      checkable=True)
        self.watcher_action.setChecked(bool(self.settings.get("watcher_enabled")))
        self.watcher_action.triggered.connect(self._toggle_watcher)
        self.menu.addAction(self.watcher_action)
        self.menu.addAction(QAction("Wächter-Ordner hinzufügen…", self.menu,
                                    triggered=self._add_watch_dir))

        self.menu.addSeparator()
        self.menu.addAction(QAction("Beenden", self.menu, triggered=self.app.quit))

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.menu.popup(self.tray.geometry().center())

    # ── Aktionen ────────────────────────────────────────────────────
    def add_task_dialog(self) -> None:
        action, ok = QInputDialog.getItem(
            None, "CloudLockFixer", "Aktion wählen:",
            ["Umbenennen", "Verschieben", "Löschen"], 0, False)
        if not ok:
            return
        src = QFileDialog.getExistingDirectory(None, "Ordner wählen")
        if not src:
            return
        if action == "Umbenennen":
            new, ok = QInputDialog.getText(None, "Umbenennen", "Neuer Name:")
            if not ok or not new.strip():
                return
            task = Task(chain=[Step(op="rename", src=src, arg=new.strip())])
        elif action == "Verschieben":
            dst_parent = QFileDialog.getExistingDirectory(None, "Zielordner wählen")
            if not dst_parent:
                return
            name = os.path.basename(src.rstrip("/\\"))
            task = Task(chain=[Step(op="move", src=src,
                                    arg=os.path.join(dst_parent, name))])
        else:
            if QMessageBox.question(None, "Löschen",
                                    f"'{src}' verzögert löschen?") != QMessageBox.Yes:
                return
            task = Task(chain=[Step(op="delete", src=src)])
        self.queue.add(task)
        self._refresh_status()
        self.tray.showMessage("CloudLockFixer",
                              f"Eingereiht: {task.describe()}",
                              _make_icon(), 4000)

    def run_async(self, force_pause: bool) -> None:
        if self._running:
            return
        self._running = True
        self._set_status("läuft…")

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
                                  f"{s['done']} Aktion(en) erledigt.",
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

    # ── Status ──────────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self.status_action.setText(text)
        self.tray.setToolTip(f"CloudLockFixer — {text}")

    def _refresh_status(self) -> None:
        self.queue.load()
        n = len(self.queue.pending)
        failed = sum(1 for t in self.queue.tasks
                     if t.status == "pending" and t.retry_count > 0)
        txt = "keine offenen Aufgaben" if n == 0 else f"{n} offen ({failed} mit Fehlversuch)"
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
        if checked:
            self.watcher.watch_dirs = self.settings.get("watch_dirs", [])
            self.watch_timer.start(int(self.watcher.window_s * 1000))
        else:
            self.watch_timer.stop()

    def _add_watch_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(None, "Ordner für Präventiv-Wächter")
        if not d:
            return
        dirs = self.settings.get("watch_dirs", [])
        if d not in dirs:
            dirs.append(d)
            self.settings["watch_dirs"] = dirs
            settings.save(self.settings)
            self.watcher.watch_dirs = dirs
        self.tray.showMessage("CloudLockFixer", f"Wächter-Ordner: {d}",
                              _make_icon(), 3000)

    def _watcher_tick(self) -> None:
        if self._watch_running:
            return
        self._watch_running = True

        def job():
            try:
                self.watcher.tick()
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
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Single-Instance-Guard
    from PySide6.QtCore import QSharedMemory
    guard = QSharedMemory("CloudLockFixer_singleton")
    if not guard.create(1):
        QMessageBox.information(None, "CloudLockFixer", "Läuft bereits.")
        return 0
    app._clf_guard = guard  # Referenz halten

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "CloudLockFixer", "Kein System-Tray verfügbar.")
        return 1

    TrayApp(app)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
