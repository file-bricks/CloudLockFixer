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

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QAction, QActionGroup, QColor, QDesktopServices, QIcon, QKeySequence, QPainter, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QMenu, QMessageBox, QPushButton, QSystemTrayIcon,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from . import autostart, contextmenu, settings, watcher, __version__
from .i18n import t
from .models import Queue, Step, Task
from .paths import data_dir, log_file
from .providers import WATCHER_TICK_MS, available_providers, provider_for
from .worker import run_once

log = logging.getLogger("clf")

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
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(8, 26, 28, 26)
    p.drawEllipse(26, 18, 30, 28)
    p.drawRoundedRect(10, 38, 46, 16, 8, 8)
    p.setPen(QColor("white"))
    f = p.font()
    f.setBold(True)
    f.setPointSize(13)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "↻")
    p.end()
    return QIcon(pm)


class _Signals(QObject):
    done = Signal(dict)




class ShortcutsDialog(QDialog):
    """Barrierefreier Referenzdialog für alle Tastaturkürzel und Navigationshilfen (WCAG 2.1 AA / BITV 2.0)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        title = t("shortcuts_dialog_title")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        desc = t("shortcuts_dialog_desc")
        self.setAccessibleDescription(desc)
        self.setMinimumSize(620, 480)
        self.resize(680, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QLabel(f"<h3>⌨️ {title}</h3>")
        layout.addWidget(header)

        sub = QLabel(desc)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #555555; margin-bottom: 4px;")
        layout.addWidget(sub)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            t("shortcuts_col_scope"),
            t("shortcuts_col_shortcut"),
            t("shortcuts_col_action"),
        ])
        self.tree.setColumnCount(3)
        self.tree.setAccessibleName(title)
        self.tree.setAccessibleDescription(desc)
        self.tree.setAlternatingRowColors(True)

        categories = [
            (
                t("shortcuts_group_queue"),
                [
                    ("Ctrl+O", t("add_task")),
                    ("F5", t("run_now")),
                    ("Ctrl+Shift+F5", t("run_now_with_pause")),
                    ("Ctrl+R", t("retry_failed_tasks")),
                ],
            ),
            (
                t("shortcuts_group_folders"),
                [
                    ("Ctrl+D", t("open_data_folder")),
                    ("Ctrl+S", t("menu_export_snapshot")),
                ],
            ),
            (
                t("shortcuts_group_help"),
                [
                    ("F1", t("shortcuts_menu_item")),
                    ("Shift+F1", t("about_menu_item")),
                ],
            ),
            (
                t("shortcuts_group_system"),
                [
                    ("Ctrl+Q", t("quit_label")),
                    ("Esc", t("shortcuts_nav_escape")),
                    ("↑ / ↓", t("shortcuts_nav_arrows")),
                ],
            ),
        ]

        for cat_title, items in categories:
            cat_item = QTreeWidgetItem(self.tree, [cat_title, "", ""])
            cat_item.setExpanded(True)
            for sc, act in items:
                QTreeWidgetItem(cat_item, ["", sc, act])

        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tree)

        note = QLabel(t("shortcuts_a11y_note"))
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 11px; color: #666666;")
        layout.addWidget(note)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.close_btn = QPushButton(t("close_button"))
        self.close_btn.setDefault(True)
        self.close_btn.setAutoDefault(True)
        self.close_btn.clicked.connect(self.accept)
        btn_box.addWidget(self.close_btn)
        layout.addLayout(btn_box)

        self.close_btn.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)


class AboutDialog(QDialog):
    """Barrierefreier Über-Dialog mit Version, Lizenz, Invarianten und Barrierefreiheit."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        title = t("about_dialog_title")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        desc = t("about_dialog_desc")
        self.setAccessibleDescription(desc)
        self.setMinimumSize(500, 360)
        self.resize(540, 390)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon = _make_icon()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(48, 48))
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel(f"<h2>CloudLockFixer v{__version__}</h2>")
        title_layout.addWidget(title_label)
        sub_label = QLabel(desc)
        sub_label.setWordWrap(True)
        sub_label.setStyleSheet("color: #444444; font-weight: bold;")
        title_layout.addWidget(sub_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        info_group = QGroupBox("System & Architektur")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)

        lbl_license = QLabel(t("about_license_label"))
        lbl_egress = QLabel(t("about_zero_egress_label"))
        lbl_egress.setWordWrap(True)
        lbl_a11y = QLabel(t("about_a11y_label"))
        lbl_platform = QLabel("Plattform: Python 3.10+ & PySide6 / Qt6 (Windows, Linux, macOS)")

        for lbl in (lbl_license, lbl_egress, lbl_a11y, lbl_platform):
            info_layout.addWidget(lbl)

        layout.addWidget(info_group)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.close_btn = QPushButton(t("close_button"))
        self.close_btn.setDefault(True)
        self.close_btn.setAutoDefault(True)
        self.close_btn.clicked.connect(self.accept)
        btn_box.addWidget(self.close_btn)
        layout.addLayout(btn_box)

        self.close_btn.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)


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
        self.menu.setAccessibleName(t("menu_accessible_name"))
        self.menu.setAccessibleDescription(t("menu_accessible_desc"))
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.run_async(False, apply_backoff=True))
        self._apply_interval()

        self.providers = available_providers()
        self.watchers: dict[str, watcher.PreventiveWatcher] = {}
        watch_dirs = self.settings.get("watch_dirs", [])
        for prov in self.providers:
            # Virtual-Mount-Provider (Google Drive, pCloud) nie als Wächter
            # registrieren: ihr Prozess-Kill würde den Laufwerks-Mount abreißen.
            if prov.mount_type == "virtual":
                continue
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
        QTimer.singleShot(3000, lambda: self.run_async(False, apply_backoff=True))

    # ── Menü ────────────────────────────────────────────────────────
    def show_shortcuts_dialog(self) -> None:
        dlg = ShortcutsDialog()
        dlg.exec()

    def show_about_dialog(self) -> None:
        dlg = AboutDialog()
        dlg.exec()

    def retranslate_ui(self) -> None:
        self.menu.setAccessibleName(t("menu_accessible_name"))
        self.menu.setAccessibleDescription(t("menu_accessible_desc"))
        self._build_menu()
        self._refresh_status()

    def _build_menu(self) -> None:
        self.menu.clear()
        self.status_action = QAction("…")
        self.status_action.setEnabled(False)
        self.status_action.setStatusTip(t("status_accessible_name"))
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.add_task_action = QAction(t("add_task"), self.menu,
                                       triggered=self.add_task_dialog)
        self.add_task_action.setShortcut(QKeySequence("Ctrl+O"))
        self.add_task_action.setStatusTip(t("add_task"))
        self.menu.addAction(self.add_task_action)

        self.run_now_action = QAction(t("run_now"), self.menu,
                                    triggered=lambda: self.run_async(False, apply_backoff=False))
        self.run_now_action.setShortcut(QKeySequence("F5"))
        self.run_now_action.setStatusTip(t("run_now"))
        self.menu.addAction(self.run_now_action)

        self.run_now_pause_action = QAction(t("run_now_with_pause"), self.menu,
                                          triggered=lambda: self.run_async(True, apply_backoff=False))
        self.run_now_pause_action.setShortcut(QKeySequence("Ctrl+Shift+F5"))
        self.run_now_pause_action.setStatusTip(t("run_now_with_pause"))
        self.menu.addAction(self.run_now_pause_action)

        self.retry_failed_action = QAction(t("retry_failed_tasks"), self.menu,
                                           triggered=self._retry_failed_tasks)
        self.retry_failed_action.setShortcut(QKeySequence("Ctrl+R"))
        self.retry_failed_action.setStatusTip(t("retry_failed_tasks"))
        self.retry_failed_action.setEnabled(False)
        self.menu.addAction(self.retry_failed_action)

        self.open_data_action = QAction(t("open_data_folder"), self.menu,
                                    triggered=self._open_data_dir)
        self.open_data_action.setShortcut(QKeySequence("Ctrl+D"))
        self.open_data_action.setStatusTip(t("open_data_folder"))
        self.menu.addAction(self.open_data_action)

        self.export_snapshot_action = QAction(t("menu_export_snapshot"), self.menu,
                                    triggered=self._export_snapshot)
        self.export_snapshot_action.setShortcut(QKeySequence("Ctrl+S"))
        self.export_snapshot_action.setStatusTip(t("menu_export_snapshot"))
        self.menu.addAction(self.export_snapshot_action)

        self.interval_menu = self.menu.addMenu(t("interval_menu"))
        self.interval_menu.setAccessibleName(t("interval_menu"))
        grp = QActionGroup(self.menu)
        grp.setExclusive(True)
        cur = settings.get_interval_min(self.settings)
        for m in INTERVAL_CHOICES_MIN:
            label = f"{m} min" if m < 60 else (f"{m // 60} h" if m % 60 == 0
                                               else f"{m / 60:.1f} h")
            a = QAction(label, self.menu, checkable=True)
            a.setChecked(m == cur)
            a.triggered.connect(lambda _=False, mm=m: self._set_interval(mm))
            grp.addAction(a)
            self.interval_menu.addAction(a)

        self.max_retries_menu = self.menu.addMenu(t("max_retries_menu"))
        self.max_retries_menu.setAccessibleName(t("max_retries_menu"))
        retry_grp = QActionGroup(self.menu)
        retry_grp.setExclusive(True)
        cur_retries = settings.get_max_retries(self.settings)

        a_unlimited = QAction(t("max_retries_unlimited"), self.menu, checkable=True)
        a_unlimited.setChecked(cur_retries is None)
        a_unlimited.triggered.connect(lambda: self._set_max_retries(None))
        retry_grp.addAction(a_unlimited)
        self.max_retries_menu.addAction(a_unlimited)

        for limit in [3, 5, 10, 20]:
            a_lim = QAction(str(limit), self.menu, checkable=True)
            a_lim.setChecked(cur_retries == limit)
            a_lim.triggered.connect(lambda _=False, lim=limit: self._set_max_retries(lim))
            retry_grp.addAction(a_lim)
            self.max_retries_menu.addAction(a_lim)

        self.notifications_action = QAction(t("notifications_label"), self.menu,
                                            checkable=True)
        self.notifications_action.setChecked(settings.get_notifications_enabled(self.settings))
        self.notifications_action.triggered.connect(self._toggle_notifications)
        self.menu.addAction(self.notifications_action)

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
        self.lang_menu = self.menu.addMenu(t("language_menu"))
        self.lang_menu.setAccessibleName(t("language_menu"))
        lang_grp = QActionGroup(self.menu)
        lang_grp.setExclusive(True)
        cur_lang = self.settings.get("language", "auto")
        for code, label in [
            ("auto", t("language_auto")),
            ("de", "Deutsch"),
            ("en", "English"),
            ("es", "Español"),
            ("zh", "中文 (简体)"),
            ("ja", "日本語"),
            ("ru", "Русский"),
        ]:
            a = QAction(label, self.menu, checkable=True)
            a.setChecked(code == cur_lang)
            a.triggered.connect(lambda _=False, c=code: self._set_language(c))
            lang_grp.addAction(a)
            self.lang_menu.addAction(a)

        self.menu.addSeparator()

        self.shortcuts_action = QAction(t("shortcuts_menu_item"), self.menu,
                                        triggered=self.show_shortcuts_dialog)
        self.shortcuts_action.setShortcut(QKeySequence("F1"))
        self.shortcuts_action.setStatusTip(t("shortcuts_menu_item"))
        self.menu.addAction(self.shortcuts_action)

        self.about_action = QAction(t("about_menu_item"), self.menu,
                                    triggered=self.show_about_dialog)
        self.about_action.setShortcut(QKeySequence("Shift+F1"))
        self.about_action.setStatusTip(t("about_menu_item"))
        self.menu.addAction(self.about_action)

        self.menu.addSeparator()
        self.quit_action = QAction(t("quit_label"), self.menu,
                                   triggered=self.app.quit)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.setStatusTip(t("quit_label"))
        self.menu.addAction(self.quit_action)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.menu.popup(self.tray.geometry().center())

    # ── Aktionen ────────────────────────────────────────────────────
    def _choose_action(self) -> str | None:
        action, ok = QInputDialog.getItem(
            None, "CloudLockFixer", t("action_choose"),
            [t("action_rename"), t("action_move"), t("action_delete")], 0, False)
        return action if ok else None

    def _choose_new_name(self) -> str | None:
        new_name, ok = QInputDialog.getText(
            None, t("action_rename"), t("rename_prompt"))
        if not ok:
            return None
        new_name = new_name.strip()
        return new_name or None

    def _choose_existing_folder(self, title_key: str) -> str | None:
        path = QFileDialog.getExistingDirectory(None, t(title_key))
        return path or None

    def _choose_existing_file(self) -> str | None:
        path, _ = QFileDialog.getOpenFileName(None, t("choose_file"))
        return path or None

    def _confirm_delete(self, src: str) -> bool:
        return QMessageBox.question(
            None, t("confirm_delete_title"), t("confirm_delete", src=src)
        ) == QMessageBox.StandardButton.Yes

    def _choose_source_path(self) -> str | None:
        source_kind, ok = QInputDialog.getItem(
            None, "CloudLockFixer", t("source_kind_choose"),
            [t("source_kind_folder"), t("source_kind_file")], 0, False)
        if not ok:
            return None
        if source_kind == t("source_kind_file"):
            return self._choose_existing_file()
        return self._choose_existing_folder("choose_folder")

    def add_task_dialog(self) -> None:
        action = self._choose_action()
        if not action:
            return
        src = self._choose_source_path()
        if not src:
            return
        if action == t("action_rename"):
            new = self._choose_new_name()
            if not new:
                return
            task = Task(chain=[Step(op="rename", src=src, arg=new)])
        elif action == t("action_move"):
            dst_parent = self._choose_existing_folder("choose_target")
            if not dst_parent:
                return
            name = os.path.basename(src.rstrip("/\\"))
            task = Task(chain=[Step(op="move", src=src,
                                    arg=os.path.join(dst_parent, name))])
        else:
            if not self._confirm_delete(src):
                return
            task = Task(chain=[Step(op="delete", src=src)])
        self.queue.add(task)
        self._refresh_status()
        self.tray.showMessage("CloudLockFixer",
                              t("queued_notification", desc=task.describe()),
                              _make_icon(), 4000)

    def run_async(self, force_pause: bool = False, apply_backoff: bool = False) -> None:
        if self._running:
            return
        self._running = True
        self._set_status(t("status_running"))

        def job():
            try:
                s = run_once(
                    self.queue,
                    force_pause=force_pause,
                    max_retries=settings.get_max_retries(self.settings),
                    apply_backoff=apply_backoff,
                    backoff_base_sec=settings.get_backoff_base(self.settings),
                    backoff_max_sec=settings.get_backoff_max(self.settings),
                    backoff_multiplier=settings.get_backoff_multiplier(self.settings),
                )
            except Exception as e:  # pragma: no cover
                log.exception("Worker run failed")
                s = {"error": str(e)}
            self.sig.done.emit(s)

        threading.Thread(target=job, daemon=True).start()

    def _on_done(self, s: dict) -> None:
        self._running = False
        self._refresh_status()
        if not settings.get_notifications_enabled(self.settings):
            return

        if s.get("done"):
            self.tray.showMessage("CloudLockFixer",
                                  t("actions_done", n=s["done"]),
                                  _make_icon(), 4000)

        perm = s.get("failed_permanent", 0)
        blocked = s.get("blocked", 0)
        if perm > 0 and blocked > 0:
            self.tray.showMessage("CloudLockFixer",
                                  t("tasks_failed_and_blocked_toast",
                                    count=perm + blocked, permanent=perm, blocked=blocked),
                                  _make_icon("#d32f2f"), 6000)
        elif perm > 0:
            self.tray.showMessage("CloudLockFixer",
                                  t("tasks_failed_permanent_toast", n=perm),
                                  _make_icon("#d32f2f"), 6000)
        elif blocked > 0:
            self.tray.showMessage("CloudLockFixer",
                                  t("tasks_blocked_toast", n=blocked),
                                  _make_icon("#d32f2f"), 6000)

    def _toggle_autostart(self, checked: bool) -> None:
        ok = autostart.enable() if checked else autostart.disable()
        if not ok:
            self.autostart_action.setChecked(autostart.is_enabled())
            self._show_setting_change_error(t("autostart_label"))

    def _set_interval(self, minutes: int) -> None:
        settings.set_interval_min(self.settings, minutes)
        self._apply_interval()

    def _apply_interval(self) -> None:
        minutes = settings.get_interval_min(self.settings)
        self.timer.start(minutes * 60 * 1000)

    def _set_max_retries(self, limit: int | None) -> None:
        settings.set_max_retries(self.settings, limit)

    def _toggle_notifications(self, checked: bool) -> None:
        settings.set_notifications_enabled(self.settings, checked)

    def _export_snapshot(self) -> None:
        from .snapshot import export_snapshot
        try:
            out_path = export_snapshot(self.data_dir)
            if settings.get_notifications_enabled(self.settings):
                self.tray.showMessage(
                    "CloudLockFixer",
                    t("snapshot_exported", path=out_path.name),
                    QSystemTrayIcon.MessageIcon.Information if hasattr(QSystemTrayIcon, "MessageIcon") else QSystemTrayIcon.Information,
                    4000,
                )
        except Exception as exc:
            log.warning("Fehler beim Exportieren des Snapshots: %s", exc)

    def _open_data_dir(self) -> None:
        # QDesktopServices öffnet den Ordner auch unter Linux/macOS
        # (os.startfile existiert nur unter Windows).
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))

    def _set_language(self, code: str) -> None:
        self.settings["language"] = code
        settings.save(self.settings)
        from . import i18n
        resolved = settings.resolve_language(self.settings)
        i18n.set_language(resolved)
        self.retranslate_ui()
        self.tray.showMessage("CloudLockFixer", t("restart_required"),
                              _make_icon(), 4000)

    # ── Status ──────────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self.status_action.setText(text)
        self.tray.setToolTip(f"CloudLockFixer — {text}")

    def _refresh_status(self) -> None:
        if not self._running:
            self.queue.load()
        n, retrying, failed = self.queue.status_counts()
        txt = (t("status_no_tasks") if n == 0 and failed == 0
               else t("status_open", n=n, retrying=retrying, failed=failed))
        self._set_status(txt)
        if hasattr(self, "retry_failed_action"):
            if failed > 0:
                self.retry_failed_action.setEnabled(True)
                self.retry_failed_action.setText(
                    t("retry_failed_tasks_count", count=failed)
                )
            else:
                self.retry_failed_action.setEnabled(False)
                self.retry_failed_action.setText(t("retry_failed_tasks"))

    def _retry_failed_tasks(self) -> None:
        retried = self.queue.retry_all()
        self._refresh_status()
        if retried:
            self.tray.showMessage("CloudLockFixer",
                                  t("retried_notification", count=len(retried)),
                                  _make_icon(), 4000)
            self.run_async(False, apply_backoff=False)

    # ── P2: Kontextmenü ─────────────────────────────────────────────
    def _toggle_context(self, checked: bool) -> None:
        ok = contextmenu.install() if checked else contextmenu.uninstall()
        if not ok:
            self.context_action.setChecked(contextmenu.is_installed())
            self._show_setting_change_error(t("context_menu_label"))

    @staticmethod
    def _show_setting_change_error(setting: str) -> None:
        """Make a rejected tray setting explicit and keyboard-accessible."""
        QMessageBox.warning(
            None,
            "CloudLockFixer",
            t("setting_change_failed", setting=setting),
        )

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
            elif prov and prov.mount_type != "virtual":
                # Virtual-Mount-Provider (Google Drive, pCloud) bekommen keinen
                # Präventiv-Wächter — ihr Prozess-Kill risse den Mount ab.
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
                log.exception("Preventive watcher tick failed")
            finally:
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
