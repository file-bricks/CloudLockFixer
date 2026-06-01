# CloudLockFixer — Roadmap

## v1.0.0 (erledigt)

- Kernfunktionalität: copy+delete-Workaround für Cloud-gesperrte Dateien
- OneDrive-Provider (Erkennung, Pause/Resume via taskkill)
- Queue-System (queue.json + queue.txt für Menschen/LLMs)
- Tray-App (PySide6) mit periodischer Ausführung
- CLI für Scripting/LLM-Integration
- Explorer-Kontextmenü (HKCU, kaskadierend)
- Präventiv-Wächter (Änderungsrate-basiertes Pausieren)
- Autostart via Registry
- PyInstaller-Build

## v1.1.0 — i18n + Bugfixes (erledigt)

- [x] Bugfixes: Verify-Cleanup, Watcher-Resume, Queue-Race-Condition
- [x] Internationalisierung: Deutsch + Englisch
- [x] Sprachauswahl im Tray-Menü (de/en/auto)
- [x] Systemsprache-Erkennung via locale

## v1.2.0 — Windows Multicloud (erledigt)

- [x] Google Drive Provider (GoogleDriveFS, virtueller Mount)
- [x] Dropbox Provider
- [x] iCloud Provider
- [x] Auto-Discovery installierter Cloud-Sync-Clients
- [x] Dynamische Provider-Anzeige im Tray
- [x] Virtual-mount Guard (kein Pause für gemountete Laufwerke)
- [x] Multi-Provider Präventiv-Wächter

## v2.0.0 — Cross-Platform

- [ ] Linux-Support (siehe PORTIERUNGSPLAN.md)
- [ ] macOS-Support (siehe PORTIERUNGSPLAN.md)
- [ ] Plattform-Abstraktion für Prozessmanagement
- [ ] Plattform-Abstraktion für Autostart/Kontextmenü
- [ ] CI/CD für Multi-Plattform-Builds

## Langfristig

- [ ] Weitere Cloud-Provider (Box, Nextcloud, pCloud, Synology Drive)
- [ ] Konfigurierbares Retry-Verhalten (Exponential Backoff, max Retries)
- [ ] Benachrichtigungen (System-Toast bei Dauerfehler)
- [ ] Web-Dashboard / Remote-Status
- [ ] Plugin-System für Community-Provider
