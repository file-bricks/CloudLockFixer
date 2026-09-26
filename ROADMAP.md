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

## Windows Store Release-Vorbereitung (erledigt 2026-09-23)

- [x] Packaging-Manifest & Identity (`store_package.json`, `Geiger.CloudLockFixer`, `0.2.3.0`, `runFullTrust`)
- [x] Desktop Bridge Manifest (`store_package/CloudLockFixer/AppxManifest.xml`)
- [x] Vollständiger Kachel- und Icon-Satz (`icon_44x44.png` bis `icon_310x310.png` und `StoreLogo.png`)
- [x] Bilinguale Store-Listings mit maximal 7 Keywords nach Policy 10.1.3 (`STORE_LISTING.md`)
- [x] Zero-Egress Datenschutzerklärung (`PRIVACY_POLICY.md`) und Support-Leitfaden (`SUPPORT.md`)
- [x] Staging-Verzeichnis `releases/windowsstore/` mit Build- und WACK-Protokollen
- [x] 16:9-Präsentationsscreenshot-Generator (`scripts/generate_store_screenshots.py`)
- [x] Automatisierte Validierungs- und Test-Suite (`scripts/check_store_readiness.py`, `tests/test_store_readiness.py`)

## v2.0.0 — Cross-Platform

- [x] Linux-Source-Support auf Smoke-/CI-Niveau (DONE 2026-07-06; siehe
  `PORTIERUNGSPLAN.md` und `tests/source_platform_smoke.py`)
- [x] macOS-Source-Support auf Smoke-/CI-Niveau (DONE 2026-07-06; siehe
  `PORTIERUNGSPLAN.md` und `tests/source_platform_smoke.py`)
- [x] Plattform-Abstraktion für Prozessmanagement (Task 169) (DONE 2026-09-26; `src/cloudlockfixer/process.py`)
- [x] Plattform-Abstraktion für Autostart/Kontextmenü (Task 170)
  - [x] Linux-XDG-Autostart auf Source-Ebene (DONE 2026-07-18)
  - [x] macOS-LaunchAgent auf Source-Ebene (DONE 2026-07-22)
  - [x] Linux-/macOS-Kontextmenü (DONE 2026-09-21; Nautilus-Skripte, KDE ServiceMenu, macOS Services)
- [x] CI für Linux/macOS-Source-Smokes
- [ ] CI/CD für native Multi-Plattform-Builds und Paketierung (Task 171)

## v2.x — Release-Scope nach dem Source-Support

- [ ] Native Linux-Integration jenseits des Source-Smokes entscheiden (Task 171)
- [ ] Native macOS-App-/Paketierungsweg entscheiden (Task 171)
- [x] Linux-XDG-Autostart auf Source-Ebene
- [x] macOS-LaunchAgent auf Source-Ebene
- [x] Linux-/macOS-Kontextmenüs (Task 170, DONE 2026-09-21)

## Verifizierter Source-Stand 2026-08-11

- **Provider-Vertrag:** Auto-Discovery für acht Provider (OneDrive, Google Drive,
  Dropbox, Box, Nextcloud, pCloud, Synology Drive und iCloud); Google Drive und
  pCloud sind Virtual Mounts und werden nicht pausiert.
- **Queue-/Tray-Vertrag:** `rename`/`move`/`delete`, Ketten mit `&&`, Menüaktion
  „Open data folder“ statt eines behaupteten Queue-/Log-Viewers.
- **Retry-Vertrag:** Default unbegrenzt: retryfähige Tasks bleiben pending.
  Ein endliches Limit ist nur ein expliziter Aufruferparameter.
- **Nachweis:** 167 Tests gesammelt; der Status ist Source-/CI-Evidenz. Native
  Paketierung, echte Client-Prozess-Smokes und Security-Freigabe bleiben offen.

## Langfristig

- [x] Weitere Cloud-Provider (Box, Nextcloud, pCloud, Synology Drive)
  - Box erledigt 2026-06-17
  - Nextcloud erledigt 2026-06-16
  - pCloud erledigt 2026-06-28
  - Synology Drive erledigt 2026-06-30
- [x] Konfigurierbares Retry-Verhalten (Backoff und persistierbares Limit)
  in settings.py / worker.py / cli.py / tray.py. Der Default bleibt
  unbegrenzt; persistierbares Limit per Tray und CLI `--max-retries`
  (erledigt 2026-09-11).
- [x] Strukturierte Ausgänge für Worker-Fehler: retryfähige Fehler bleiben
  `pending`; deterministische Zielkonflikte werden als `blocked` gespeichert;
  ein explizites Limit bleibt `permanent`/`failed`.
- [x] Benachrichtigungen (System-Toast bei Dauerfehler und blockierten Tasks
  via QSystemTrayIcon, konfigurierbar über Tray-Menü, erledigt 2026-09-11).
- [ ] Web-Dashboard / Remote-Status
- [ ] Plugin-System für Community-Provider
- [ ] Konfigurierbares Retry-Verhalten (Backoff und persistierbares Limit) (Task 172).
  Der aktuelle Default bleibt unbegrenzt; ein Aufrufer kann bereits ein
  endliches Limit übergeben.
- [x] Strukturierte Ausgänge für Worker-Fehler: retryfähige Fehler bleiben
  `pending`; deterministische Zielkonflikte werden als `blocked` gespeichert;
  ein explizites Limit bleibt `permanent`/`failed`.
- [ ] Benachrichtigungen (System-Toast bei Dauerfehler) (Task 173)
- [ ] Web-Dashboard / Remote-Status (Task 173)
- [ ] Plugin-System für Community-Provider (Task 173)

## TASKWRITER-REVIEW-LOG — 2026-09-05

- Der historische Source-Stand vom 2026-08-11 bleibt mit 167 Tests datiert;
  der aktuelle Checkout wurde separat mit 205 gesammelten und bestandenen
  Tests verifiziert. README, README.de, llms.txt und CHANGELOG führen bereits
  die aktuelle Zahl 205.
- `main` ist sauber und zu `origin/main` synchron (`287d9f4`). Die aktuellen
  GitHub-Test- und Source-Smoke-Runs sind erfolgreich; native Installer,
  echte Cloud-Client-Prozesse, Security-Freigabe und Veröffentlichung bleiben
  nach `RELEASE_GATE.md` offen.
- Tasks 165–173 sind als evidenzbasierte Folgeaufträge angelegt. Es wurden
  keine Provider-Prozesse, Registry-Einträge, Desktop-Kontextmenüs, Builds,
  Signaturen oder Uploads ausgeführt.
