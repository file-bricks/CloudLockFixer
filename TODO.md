# CloudLockFixer — Aktive Aufgaben

## i18n (Internationalisierung)

- [ ] i18n-Modul erstellen (`src/cloudlockfixer/i18n.py`, Dict-basiert, de+en)
- [ ] `settings.py`: `resolve_language()` für "auto"/"de"/"en"
- [ ] `tray.py`: ~30 UI-Strings mit `t()` wrappen, Sprach-Submenü
- [ ] `cli.py`: ~15 Strings mit `t()` wrappen, Language vor argparse setzen
- [ ] `models.py`: `_TXT_HEADER` und Fehler-Prefix übersetzen
- [ ] `contextmenu.py`: 3 Registry-Labels übersetzen
- [ ] `worker.py` + `watcher.py`: Deutsche Log-Messages → Englisch
- [ ] `tests/test_i18n.py`: Coverage-Tests (alle Keys de+en, Fallback, detect)
- [ ] Advisor-Review + Commit + Push

## Multicloud (Windows)

- [ ] `SyncProvider` ABC: `mount_type` Property ("folder"/"virtual")
- [ ] `GoogleDriveProvider`: Erkennung via Drive-Letter-Scan, mount_type="virtual"
- [ ] `DropboxProvider`: Erkennung via %USERPROFILE%\Dropbox + info.json
- [ ] `ICloudProvider`: Erkennung via %USERPROFILE%\iCloudDrive + Registry
- [ ] `_discover_providers()`: Auto-Discovery installierter Clouds
- [ ] `worker.py`: Guard — Pause für virtual-mount Provider gesperrt
- [ ] `tray.py`: Dynamische Provider-Labels, Multi-Watcher
- [ ] `tests/test_providers_multi.py`: Provider-Tests mit Mocks
- [ ] Advisor-Review + Commit + Push

## Dokumentation

- [x] TODO.md (diese Datei)
- [x] ROADMAP.md (langfristige Planung)
- [x] PORTIERUNGSPLAN.md (Linux/macOS)
