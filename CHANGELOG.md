# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- GitHub Actions workflow for Windows smoke tests on Python 3.10, 3.11 and 3.12.
- `llms.txt` with canonical machine-readable project context.

### Geändert / Changed
- Roadmap and README test counts now reflect the current i18n and multicloud implementation.

### Behoben / Fixed
- Locale detection no longer uses Python's deprecated `locale.getdefaultlocale()`.

## [1.0.0] - 2026-05-30

### Hinzugefügt / Added
- **Core:** Verzögerte Datei-Operationen (rename / move / delete) mit
  copy+delete als universelle Primitive, umgeht den Windows-Cloud-Files-Filter
  (`cldflt`). / Delayed file operations using copy+delete to bypass `cldflt`.
- **Ketten / Chains:** 1–4 Schritte pro Task; destruktive Schritte erst nach
  Erfolg des Voraus-Schritts (kein Datenverlust). / Chains of 1–4 steps;
  destructive steps only after the preceding step succeeds.
- **Worker:** Ausführung bei Start, periodisch (Default 2 h) und manuell, mit
  Retry. / Execution on start, periodically, and on demand, with retry.
- **CLI:** `clf add --rename|--move|--delete|--chain`, `list`, `run-now`.
- **queue.txt:** Menschen-/LLM-lesbares Eingabeformat. / Human/LLM-readable input.
- **Tray (PySide6):** Task-Dialog, „Jetzt ausführen", Intervall, Autostart.
- **OneDrive-Provider:** Sync-Client für die Dauer einer Operation pausieren
  und neu starten. / Pause and restart the sync client during an operation.
- **Explorer-Kontextmenü (P2):** „verzögert umbenennen/verschieben/löschen"
  (HKCU, opt-in). / Explorer right-click context menu (opt-in).
- **Präventiv-Wächter (P3):** Beobachtet die Änderungsrate konfigurierter
  Ordner und pausiert/fortsetzt den Sync-Client (stat-only, opt-in). /
  Preventive watcher that pauses/resumes the sync client (opt-in).

### Erstveröffentlichung / Initial release
- 17 Tests grün (`pytest`). / 17 passing tests.
