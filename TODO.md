# CloudLockFixer — Aktive Aufgaben

## i18n (Internationalisierung) — erledigt v1.1.0

- [x] i18n-Modul erstellen (`src/cloudlockfixer/i18n.py`, Dict-basiert, de+en)
- [x] `settings.py`: `resolve_language()` für "auto"/"de"/"en"
- [x] `tray.py`: ~30 UI-Strings mit `t()` wrappen, Sprach-Submenü
- [x] `cli.py`: ~15 Strings mit `t()` wrappen, Language vor argparse setzen
- [x] `models.py`: `_TXT_HEADER` und Fehler-Prefix übersetzen
- [x] `contextmenu.py`: 3 Registry-Labels übersetzen
- [x] `worker.py` + `watcher.py`: Deutsche Log-Messages → Englisch
- [x] `tests/test_i18n.py`: Coverage-Tests (alle Keys de+en, Fallback, detect)
- [x] Advisor-Review + Commit + Push

## Multicloud (Windows) — erledigt v1.2.0

- [x] `SyncProvider` ABC: `mount_type` Property ("folder"/"virtual")
- [x] `GoogleDriveProvider`: Erkennung via ctypes GetVolumeInformationW, mount_type="virtual"
- [x] `DropboxProvider`: Erkennung via %USERPROFILE%\Dropbox + info.json
- [x] `ICloudProvider`: Erkennung via %USERPROFILE%\iCloudDrive
- [x] `_discover_providers()`: Lazy Auto-Discovery mit memoized Roots
- [x] `worker.py`: Guard — Pause für virtual-mount Provider gesperrt
- [x] `tray.py`: Dynamische Provider-Labels, Multi-Watcher
- [x] `tests/test_providers_multi.py`: 16 Provider-Tests mit Mocks
- [x] Advisor-Review + Commit + Push

## Dokumentation

- [x] TODO.md (diese Datei)
- [x] ROADMAP.md (langfristige Planung)
- [x] PORTIERUNGSPLAN.md (Linux/macOS)

## Erkenntnisse aus MCP-Integration (2026-05-31)

Beim Port der copy+delete-Logik in den ellmos-filecommander-mcp-Server (TypeScript) wurden folgende Punkte entdeckt:

- [x] **EBUSY als Fehlercode aufnehmen** — DONE 2026-06-01
      `_is_lock_error()` + `_LOCK_ERRNOS` in ops.py: EBUSY, EPERM, EACCES, EXDEV + WinError 32/33.
      Tests: `tests/test_ebusy_and_lock_errors.py` (TestIsLockError, 11 Tests).
- [x] **Delete-nach-Copy bei aktivem Lock** — bereits korrekt via step.copied-Flag (Retry-Mechanismus).
      Tests verifizieren: step.copied=True nach partial-move, Retry löscht nur Quelle.
- [x] **Verzeichnis-Rename mit gelockter Innendatei** — DONE 2026-06-01
      `_delete_dir_skip_locked()` in ops.py: Best-effort-Bereinigung, überspringt EBUSY-Dateien.
      `_delete_path()` nutzt es automatisch wenn `_rmtree()` mit Lock-Fehler scheitert.
      Tests: TestDeleteDirSkipLocked (5 Tests).
- [x] **Bug 4: leerer Ordner mit gesperrtem Eigen-Handle → falsches „completed"** — DONE 2026-06-13
      `_delete_dir_skip_locked()` wertete `len(locked) == 0` als Erfolg; bei einem leeren,
      am eigenen Handle gesperrten Ordner (z. B. Windows Search Indexer) gibt es keine
      gesperrte Innendatei → das verschluckte `p.rmdir()`-OSError wurde als Erfolg gewertet,
      der Worker verwarf den Task statt zu retryen. Fix: Erfolg = `not p.exists()`; eigene
      Retry-Meldung in `_delete_path()`. Tests: TestEmptyDirOwnHandleLocked (4 Tests).

## Nächste Schritte (aus ROADMAP.md)

- [ ] Test-CI beobachten und bei Bedarf Windows-spezifische Runtime-Abhängigkeiten ergänzen
- [ ] Cross-Platform: Linux-Support (siehe PORTIERUNGSPLAN.md)
- [ ] Cross-Platform: macOS-Support (siehe PORTIERUNGSPLAN.md)
- [ ] Weitere Provider: Box, Nextcloud, pCloud, Synology Drive
