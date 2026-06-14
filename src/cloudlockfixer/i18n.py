"""Minimale i18n-Unterstützung (Deutsch/Englisch) für UI-Texte.

Übersetzungskatalog als einfaches Dict — kein externes Framework nötig für zwei Sprachen.
Die aktive Sprache wird einmal beim Start gesetzt (Config oder System-Locale) und bleibt
für die Laufzeit konstant.
"""
from __future__ import annotations

import locale
from typing import Literal

Language = Literal["de", "en"]

_CATALOG: dict[str, dict[Language, str]] = {
    # -- tray.py: Status --
    "status_no_tasks": {
        "de": "keine offenen Aufgaben",
        "en": "no pending tasks",
    },
    "status_open": {
        "de": "{n} offen ({failed} mit Fehlversuch)",
        "en": "{n} pending ({failed} with retries)",
    },
    "status_running": {
        "de": "läuft…",
        "en": "running…",
    },
    "actions_done": {
        "de": "{n} Aktion(en) erledigt.",
        "en": "{n} action(s) completed.",
    },
    # -- tray.py: Menü --
    "add_task": {
        "de": "Task hinzufügen…",
        "en": "Add task…",
    },
    "run_now": {
        "de": "Jetzt ausführen",
        "en": "Run now",
    },
    "run_now_with_pause": {
        "de": "Jetzt ausführen (mit Sync-Pause)",
        "en": "Run now (with sync pause)",
    },
    "open_queue_log": {
        "de": "Queue/Log öffnen",
        "en": "Open queue/log",
    },
    "interval_menu": {
        "de": "Intervall",
        "en": "Interval",
    },
    "autostart_label": {
        "de": "Mit Windows starten",
        "en": "Start with Windows",
    },
    "context_menu_label": {
        "de": "Explorer-Kontextmenü",
        "en": "Explorer context menu",
    },
    "watcher_label": {
        "de": "Präventiv-Wächter",
        "en": "Preventive watcher",
    },
    "add_watch_dir": {
        "de": "Wächter-Ordner hinzufügen…",
        "en": "Add watcher folder…",
    },
    "quit_label": {
        "de": "Beenden",
        "en": "Quit",
    },
    # -- tray.py: Dialoge --
    "action_choose": {
        "de": "Aktion wählen:",
        "en": "Choose action:",
    },
    "action_rename": {
        "de": "Umbenennen",
        "en": "Rename",
    },
    "action_move": {
        "de": "Verschieben",
        "en": "Move",
    },
    "action_delete": {
        "de": "Löschen",
        "en": "Delete",
    },
    "choose_folder": {
        "de": "Ordner wählen",
        "en": "Choose folder",
    },
    "rename_prompt": {
        "de": "Neuer Name:",
        "en": "New name:",
    },
    "choose_target": {
        "de": "Zielordner wählen",
        "en": "Choose target folder",
    },
    "confirm_delete": {
        "de": "'{src}' verzögert löschen?",
        "en": "Delete '{src}' (deferred)?",
    },
    "confirm_delete_title": {
        "de": "Löschen",
        "en": "Delete",
    },
    "queued_notification": {
        "de": "Eingereiht:\n{desc}\n\nWird beim nächsten Lauf erledigt.",
        "en": "Queued:\n{desc}\n\nWill be processed on next run.",
    },
    # -- tray.py: Wächter --
    "watch_dir_added": {
        "de": "Wächter-Ordner: {d}",
        "en": "Watcher folder: {d}",
    },
    "watcher_dir_title": {
        "de": "Ordner für Präventiv-Wächter",
        "en": "Folder for preventive watcher",
    },
    # -- tray.py: Singleton/Tray-Check --
    "already_running": {
        "de": "Läuft bereits.",
        "en": "Already running.",
    },
    "no_tray": {
        "de": "Kein System-Tray verfügbar.",
        "en": "No system tray available.",
    },
    # -- tray.py: Sprache --
    "language_menu": {
        "de": "Sprache / Language",
        "en": "Language / Sprache",
    },
    "language_auto": {
        "de": "Auto (System)",
        "en": "Auto (System)",
    },
    "restart_required": {
        "de": "Neustart erforderlich für Sprachwechsel.",
        "en": "Restart required for language change.",
    },
    # -- cli.py --
    "cli_desc": {
        "de": "CloudLockFixer CLI",
        "en": "CloudLockFixer CLI",
    },
    "cli_add_help": {
        "de": "Task einreihen",
        "en": "Queue a task",
    },
    "cli_list_help": {
        "de": "Queue anzeigen",
        "en": "Show queue",
    },
    "cli_run_help": {
        "de": "Queue jetzt abarbeiten",
        "en": "Process queue now",
    },
    "cli_pause_help": {
        "de": "Sync-Client für den Lauf pausieren (M2)",
        "en": "Pause sync client during run (M2)",
    },
    "cli_context_help": {
        "de": "Explorer-Kontextmenü verwalten",
        "en": "Manage Explorer context menu",
    },
    "cli_gui_add_help": {
        "de": "Dialog zum Einreihen (vom Kontextmenü)",
        "en": "Queuing dialog (from context menu)",
    },
    "queue_empty": {
        "de": "Queue leer.",
        "en": "Queue empty.",
    },
    "queued_msg": {
        "de": "Eingereiht: {id}  {desc}",
        "en": "Queued: {id}  {desc}",
    },
    "invalid_chain": {
        "de": "Leere/ungültige Kette.",
        "en": "Empty/invalid chain.",
    },
    "run_summary": {
        "de": "Lauf fertig: {done} erledigt, {failed} weiterhin offen (Start: {start} offen).{paused}",
        "en": "Run complete: {done} done, {failed} still pending (start: {start} pending).{paused}",
    },
    "paused_providers": {
        "de": " Pausiert: {names}",
        "en": " Paused: {names}",
    },
    "context_installed": {
        "de": "Kontextmenü installiert.",
        "en": "Context menu installed.",
    },
    "context_install_failed": {
        "de": "Installation fehlgeschlagen.",
        "en": "Installation failed.",
    },
    "context_removed": {
        "de": "Kontextmenü entfernt.",
        "en": "Context menu removed.",
    },
    "context_remove_failed": {
        "de": "Entfernen fehlgeschlagen.",
        "en": "Removal failed.",
    },
    "context_status_installed": {
        "de": "installiert",
        "en": "installed",
    },
    "context_status_not_installed": {
        "de": "nicht installiert",
        "en": "not installed",
    },
    # -- cli.py: gui-add --
    "gui_rename_title": {
        "de": "Verzögert umbenennen",
        "en": "Deferred rename",
    },
    "gui_rename_prompt": {
        "de": "Neuer Name für:\n{src}",
        "en": "New name for:\n{src}",
    },
    "gui_move_title": {
        "de": "Zielordner wählen",
        "en": "Choose target folder",
    },
    "gui_delete_title": {
        "de": "Verzögert löschen",
        "en": "Deferred delete",
    },
    "gui_delete_confirm": {
        "de": "'{src}'\nverzögert löschen?",
        "en": "Delete '{src}'\n(deferred)?",
    },
    "gui_queued_title": {
        "de": "CloudLockFixer",
        "en": "CloudLockFixer",
    },
    "gui_queued_msg": {
        "de": "Eingereiht:\n{desc}\n\nWird beim nächsten Lauf erledigt.",
        "en": "Queued:\n{desc}\n\nWill be processed on next run.",
    },
    # -- contextmenu.py --
    "ctx_delayed_rename": {
        "de": "Verzögert umbenennen",
        "en": "Deferred rename",
    },
    "ctx_delayed_move": {
        "de": "Verzögert verschieben",
        "en": "Deferred move",
    },
    "ctx_delayed_delete": {
        "de": "Verzögert löschen",
        "en": "Deferred delete",
    },
    # -- models.py --
    "queue_txt_header": {
        "de": (
            "# CloudLockFixer — Aufgaben-Queue (eine Zeile = ein Task)\n"
            "# Syntax (Pfade mit Leerzeichen in Anführungszeichen):\n"
            "#   rename <pfad> <neuerName>\n"
            "#   move <quelle> <ziel>\n"
            "#   delete <pfad>\n"
            "#   Verkettung mit &&:   move <a> <b> && delete <c>\n"
            "# Aufgenommene Zeilen werden automatisch zu '#>' auskommentiert.\n"
        ),
        "en": (
            "# CloudLockFixer — Task Queue (one line = one task)\n"
            "# Syntax (paths with spaces in quotes):\n"
            "#   rename <path> <newName>\n"
            "#   move <source> <target>\n"
            "#   delete <path>\n"
            "#   Chain with &&:   move <a> <b> && delete <c>\n"
            "# Processed lines are automatically commented out with '#>'.\n"
        ),
    },
    "parse_error": {
        "de": "FEHLER",
        "en": "ERROR",
    },
}

_current: Language = "de"


def detect_language() -> Language:
    """Sprache aus System-Locale ableiten (Fallback: Deutsch)."""
    try:
        lang, _ = locale.getlocale()
        if lang and lang.lower().startswith("en"):
            return "en"
    except Exception:
        # locale.Error (Subclass von Exception) und ValueError/TypeError
        # bei ungültiger oder nicht gesetzter System-Locale abfangen.
        pass
    return "de"


def set_language(lang: Language) -> None:
    global _current
    _current = lang


def get_language() -> Language:
    return _current


def t(key: str, **kwargs: object) -> str:
    """Übersetze einen Schlüssel in die aktive Sprache."""
    entry = _CATALOG.get(key)
    if entry is None:
        return key
    text = entry.get(_current) or entry.get("de") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def available_keys() -> list[str]:
    return sorted(_CATALOG.keys())
