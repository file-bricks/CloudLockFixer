# -*- coding: utf-8 -*-
"""Automatisierte Vertragstests für UX, Barrierefreiheit und Tastatur-Ergonomie
gemäß WCAG 2.1 AA und BITV 2.0 für CloudLockFixer.

Prüft:
- Hauptmenü-Deklaration mit barrierefreien Namen und Beschreibungen
- Globale Tastenkürzel und Accelerators auf allen Primäraktionen (Ctrl+O, F5, Ctrl+Shift+F5, Ctrl+R, Ctrl+D, Ctrl+S, F1, Shift+F1, Ctrl+Q)
- Barrierefreier Tastaturkürzel-Referenzdialog (ShortcutsDialog) mit hierarchischen Kategorien
- Strukturierter Über-Dialog (AboutDialog) mit Version 0.2.3, MIT-Lizenz, Zero-Egress Reassurance und Barrierefreiheitsdeklaration
- Escape-Tastatur-Handler auf allen barrierefreien Dialogen
- Dynamische Neuübersetzung aller A11y-Attribute und Menütexte
- Echte deutsche Umlaute in allen End-User-Texten (ä, ö, ü, Ä, Ö, Ü, ß)
- 100% Übersetzungsparität über alle 6 Sprachen (de, en, es, zh, ja, ru)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QDialog, QLabel

from cloudlockfixer import i18n, settings, tray
from cloudlockfixer.i18n import _CATALOG, SUPPORTED_LANGUAGES
from cloudlockfixer.tray import AboutDialog, ShortcutsDialog, TrayApp


def _get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


@pytest.fixture
def clean_tray(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tray, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tray, "available_providers", lambda: [])
    i18n.set_language("de")
    app = _get_qapp()
    t_app = TrayApp(app)
    try:
        yield t_app
    finally:
        t_app.timer.stop()
        t_app.watch_timer.stop()
        t_app.tray.hide()
        i18n.set_language("de")


def test_menu_accessible_attributes_and_retranslation(clean_tray):
    """Menü besitzt deklarierte Accessible Names und Descriptions in aktiver Sprache."""
    t_app = clean_tray
    assert t_app.menu.accessibleName() == "CloudLockFixer Hauptmenü"
    assert "Cloud-Sync-Dateisperren" in t_app.menu.accessibleDescription()

    # Retranslate to English
    i18n.set_language("en")
    t_app.retranslate_ui()
    assert t_app.menu.accessibleName() == "CloudLockFixer Main Menu"
    assert "cloud sync file locks" in t_app.menu.accessibleDescription()

    # Retranslate back to German
    i18n.set_language("de")
    t_app.retranslate_ui()
    assert t_app.menu.accessibleName() == "CloudLockFixer Hauptmenü"


def test_menu_actions_keyboard_shortcuts_and_accelerators(clean_tray):
    """Alle primären Aktionen besitzen globale Tastaturkürzel und Status-Hinweise."""
    t_app = clean_tray

    # Primary shortcuts
    assert t_app.add_task_action.shortcut().toString() in ("Ctrl+O", "Strg+O")
    assert t_app.run_now_action.shortcut().toString() == "F5"
    assert t_app.run_now_pause_action.shortcut().toString() in ("Ctrl+Shift+F5", "Strg+Umschalt+F5")
    assert t_app.retry_failed_action.shortcut().toString() in ("Ctrl+R", "Strg+R")
    assert t_app.open_data_action.shortcut().toString() in ("Ctrl+D", "Strg+D")
    assert t_app.export_snapshot_action.shortcut().toString() in ("Ctrl+S", "Strg+S")
    assert t_app.shortcuts_action.shortcut().toString() == "F1"
    assert t_app.about_action.shortcut().toString() in ("Shift+F1", "Umschalt+F1")
    assert t_app.quit_action.shortcut().toString() in ("Ctrl+Q", "Strg+Q")

    # Status Tips
    assert t_app.add_task_action.statusTip() == "Task hinzufügen…"
    assert t_app.run_now_action.statusTip() == "Jetzt ausführen"
    assert t_app.shortcuts_action.statusTip() == "Tastaturkürzel & Hilfe"
    assert t_app.about_action.statusTip() == "Über CloudLockFixer…"
    assert t_app.quit_action.statusTip() == "Beenden"


def test_submenus_accessible_names(clean_tray):
    """Untermenüs (Intervall, Fehlversuche, Sprache) deklarieren Accessible Names."""
    t_app = clean_tray
    assert t_app.interval_menu.accessibleName() == "Intervall"
    assert t_app.max_retries_menu.accessibleName() == "Max. Wiederholungen"
    assert t_app.lang_menu.accessibleName() == "Sprache / Language"


def test_shortcuts_dialog_structure_categories_and_accessibility():
    """ShortcutsDialog bietet kategorisierte Tastatur-Übersicht und Escape-Handler."""
    _get_qapp()
    i18n.set_language("de")
    dlg = ShortcutsDialog()

    assert dlg.windowTitle() == "Tastaturkürzel & Barrierefreiheit"
    assert dlg.accessibleName() == "Tastaturkürzel & Barrierefreiheit"
    assert "WCAG 2.1 AA" in dlg.accessibleDescription()

    # Column headers
    assert dlg.tree.headerItem().text(0) == "Bereich"
    assert dlg.tree.headerItem().text(1) == "Tastenkürzel"
    assert dlg.tree.headerItem().text(2) == "Aktion / Beschreibung"

    # Category items
    assert dlg.tree.topLevelItemCount() == 4
    cat_names = [dlg.tree.topLevelItem(i).text(0) for i in range(4)]
    assert "Queue & Warteschlange" in cat_names
    assert "Verzeichnisse & Export" in cat_names
    assert "Hilfe & Information" in cat_names
    assert "System & Navigation" in cat_names

    # Focused default close button
    assert dlg.close_btn.isDefault()
    assert dlg.close_btn.text() == "Schließen"

    # Escape key closes dialog
    escape_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(escape_event)
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_about_dialog_metadata_and_accessibility():
    """AboutDialog deklariert Version 0.2.3, Lizenz, Zero-Egress Reassurance und Escape-Handler."""
    _get_qapp()
    i18n.set_language("de")
    dlg = AboutDialog()

    assert dlg.windowTitle() == "Über CloudLockFixer"
    assert dlg.accessibleName() == "Über CloudLockFixer"
    assert "Cloud-Sync-Dateien" in dlg.accessibleDescription()

    # Dialog labels inspection
    all_labels = [w.text() for w in dlg.findChildren(QLabel)]
    dialog_text = " ".join(all_labels)

    assert "CloudLockFixer v0.2.3" in dialog_text
    assert "MIT-Lizenz" in dialog_text
    assert "100% lokal" in dialog_text
    assert "kein Netzwerk-Egress" in dialog_text
    assert "WCAG 2.1 AA" in dialog_text

    # Default button
    assert dlg.close_btn.isDefault()

    # Escape closes
    escape_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(escape_event)
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_retranslate_ui_updates_actions_text(clean_tray):
    """Laufzeit-Sprachwechsel aktualisiert alle Beschriftungen ohne Neustart."""
    t_app = clean_tray

    i18n.set_language("en")
    t_app.retranslate_ui()
    assert t_app.add_task_action.text() == "Add task…"
    assert t_app.run_now_action.text() == "Run now"
    assert t_app.shortcuts_action.text() == "Keyboard Shortcuts & Help"
    assert t_app.about_action.text() == "About CloudLockFixer…"
    assert t_app.quit_action.text() == "Quit"

    i18n.set_language("es")
    t_app.retranslate_ui()
    assert t_app.add_task_action.text() == "Añadir tarea…"
    assert t_app.run_now_action.text() == "Ejecutar ahora"
    assert t_app.quit_action.text() == "Salir"

    i18n.set_language("de")
    t_app.retranslate_ui()
    assert t_app.add_task_action.text() == "Task hinzufügen…"
    assert t_app.run_now_action.text() == "Jetzt ausführen"
    assert t_app.quit_action.text() == "Beenden"


def test_german_end_user_texts_umlauts_integrity():
    """Deutsche End-User-Texte verwenden ausnahmslos echte Umlaute (ä, ö, ü, Ä, Ö, Ü, ß)."""
    tested_keys = [
        "menu_accessible_name",
        "menu_accessible_desc",
        "status_accessible_name",
        "shortcuts_dialog_title",
        "shortcuts_dialog_desc",
        "shortcuts_menu_item",
        "about_dialog_title",
        "about_menu_item",
        "about_dialog_desc",
        "about_license_label",
        "about_zero_egress_label",
        "about_a11y_label",
        "close_button",
        "shortcuts_col_scope",
        "shortcuts_col_shortcut",
        "shortcuts_col_action",
        "shortcuts_group_queue",
        "shortcuts_group_folders",
        "shortcuts_group_help",
        "shortcuts_group_system",
        "shortcuts_nav_escape",
        "shortcuts_nav_arrows",
        "shortcuts_a11y_note",
    ]

    for key in tested_keys:
        val = _CATALOG[key]["de"]
        assert "Tastaturkuerzel" not in val
        assert "Schliessen" not in val
        assert "Ueber" not in val
        assert "Menue" not in val
        assert "gemaess" not in val
        assert "vollstaendige" not in val

    assert "ü" in _CATALOG["menu_accessible_name"]["de"]
    assert "ü" in _CATALOG["shortcuts_dialog_title"]["de"]
    assert "ß" in _CATALOG["close_button"]["de"]
    assert "Über" in _CATALOG["about_dialog_title"]["de"]


def test_six_languages_parity_for_accessibility_keys():
    """Alle neuen Barrierefreiheits-Schlüssel besitzen 100% Parität über alle 6 Sprachen."""
    tested_keys = [
        "menu_accessible_name",
        "menu_accessible_desc",
        "status_accessible_name",
        "shortcuts_dialog_title",
        "shortcuts_dialog_desc",
        "shortcuts_menu_item",
        "about_dialog_title",
        "about_menu_item",
        "about_dialog_desc",
        "about_license_label",
        "about_zero_egress_label",
        "about_a11y_label",
        "close_button",
        "shortcuts_col_scope",
        "shortcuts_col_shortcut",
        "shortcuts_col_action",
        "shortcuts_group_queue",
        "shortcuts_group_folders",
        "shortcuts_group_help",
        "shortcuts_group_system",
        "shortcuts_nav_escape",
        "shortcuts_nav_arrows",
        "shortcuts_a11y_note",
    ]

    for key in tested_keys:
        assert key in _CATALOG, f"Missing key {key} in _CATALOG"
        for lang in SUPPORTED_LANGUAGES:
            val = _CATALOG[key].get(lang)
            assert val is not None and len(str(val).strip()) > 0, (
                f"Missing or empty translation for key '{key}' in language '{lang}'"
            )
