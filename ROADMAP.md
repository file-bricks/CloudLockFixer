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

- [x] Linux-Source-Support auf Smoke-/CI-Niveau (DONE 2026-07-06; siehe
  `PORTIERUNGSPLAN.md` und `tests/source_platform_smoke.py`)
- [x] macOS-Source-Support auf Smoke-/CI-Niveau (DONE 2026-07-06; siehe
  `PORTIERUNGSPLAN.md` und `tests/source_platform_smoke.py`)
- [ ] Plattform-Abstraktion für Prozessmanagement
- [ ] Plattform-Abstraktion für Autostart/Kontextmenü
  - [x] Linux-XDG-Autostart auf Source-Ebene (DONE 2026-07-18)
  - [x] macOS-LaunchAgent auf Source-Ebene (DONE 2026-07-22)
  - [ ] Linux-/macOS-Kontextmenü
- [x] CI für Linux/macOS-Source-Smokes
- [ ] CI/CD für native Multi-Plattform-Builds und Paketierung

## v2.x — Release-Scope nach dem Source-Support

- [ ] Native Linux-Integration jenseits des Source-Smokes entscheiden
- [ ] Native macOS-App-/Paketierungsweg entscheiden
- [x] Linux-XDG-Autostart auf Source-Ebene
- [x] macOS-LaunchAgent auf Source-Ebene
- [ ] Linux-/macOS-Kontextmenüs

## Verifizierter Source-Stand 2026-08-11

- **Provider-Vertrag:** Auto-Discovery für acht Provider (OneDrive, Google Drive,
  Dropbox, Box, Nextcloud, pCloud, Synology Drive und iCloud); Google Drive und
  pCloud sind Virtual Mounts und werden nicht pausiert.
- **Queue-/Tray-Vertrag:** `rename`/`move`/`delete`, Ketten mit `&&`, Menüaktion
  „Open data folder“ statt eines behaupteten Queue-/Log-Viewers.
- **Retry-Vertrag:** Default-Cap 5; danach `failed` und nicht mehr pending.
- **Nachweis:** 165 Tests gesammelt; der Status ist Source-/CI-Evidenz. Native
  Paketierung, echte Client-Prozess-Smokes und Security-Freigabe bleiben offen.

## Langfristig

- [x] Weitere Cloud-Provider (Box, Nextcloud, pCloud, Synology Drive)
  - Box erledigt 2026-06-17
  - Nextcloud erledigt 2026-06-16
  - pCloud erledigt 2026-06-28
  - Synology Drive erledigt 2026-06-30
- [ ] Konfigurierbares Retry-Verhalten (Backoff und Cap); der aktuelle Default-Cap
  beträgt 5 Versuche und ist kein unbegrenzter Retry.
- [ ] Benachrichtigungen (System-Toast bei Dauerfehler)
- [ ] Web-Dashboard / Remote-Status
- [ ] Plugin-System für Community-Provider
