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

- [ ] **EBUSY als Fehlercode aufnehmen:** Windows gibt bei File-Locks durch andere Prozesse (inkl. Cloud-Sync) `EBUSY` zurück, nicht nur EPERM/EACCES. CLFs `ops.py` sollte EBUSY in die Retry-Trigger-Codes aufnehmen (aktuell nur EXDEV + Access Denied).
- [ ] **Delete-nach-Copy bei aktivem Lock:** Wenn die Kopie erfolgreich ist aber das Löschen des Originals mit EBUSY scheitert (Datei noch vom Sync-Client gehalten), ist das ein Teilerfolg. CLF handhabt das bereits via Queue-Retry — aber der Status sollte explizit als "kopiert, Löschung ausstehend" im queue.txt sichtbar sein.
- [ ] **Verzeichnis-Rename mit gelockter Innendatei:** Bei `fs.rename()` auf ein Verzeichnis, dessen Inhalt einen gelockten File enthält, gibt Windows EPERM (nicht EBUSY). Die copy+delete-Strategie funktioniert hier korrekt (rekursives Kopieren + rekursives Löschen), aber das Löschen des Quellverzeichnisses scheitert wenn eine Innendatei noch gelockt ist. CLFs `ops.py` sollte diesen Fall explizit behandeln.

## Nächste Schritte (aus ROADMAP.md)

- [ ] Test-CI beobachten und bei Bedarf Windows-spezifische Runtime-Abhängigkeiten ergänzen
- [ ] Cross-Platform: Linux-Support (siehe PORTIERUNGSPLAN.md)
- [ ] Cross-Platform: macOS-Support (siehe PORTIERUNGSPLAN.md)
- [ ] Weitere Provider: Box, Nextcloud, pCloud, Synology Drive
