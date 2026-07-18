# CloudLockFixer — Aktive Aufgaben

## Software-Review-Loop 2026-07-12 (Fable) — zurückgestellt (brauchen echtes Gerät/Recherche)

- [ ] P2: Synology pause/resume-Asymmetrie prüfen (providers.py:456-476):
      pause() killt cloud-drive-ui.exe UND SynologyDrive.exe, resume() startet
      nur cloud-drive-ui.exe. Am echten Synology-Prozessmodell verifizieren,
      ob der Daemon vom UI-Start mitgezogen wird — sonst bleibt Sync tot.
- [x] P2: Synology Custom-Sync-Ordner wird nicht erkannt (nur ~/SynologyDrive
      hardcodiert; providers.py:445-450). DONE 2026-07-13:
      `_read_synology_custom_roots()` scannt jetzt lokale Synology-AppData-
      Konfigurationsdateien (`*.json`/`*.conf`/`*.cfg`) nach `local_path` /
      `localPath`, akzeptiert nur existierende Pfade und ergänzt diese zur
      Default-Erkennung. Regressionen: JSON- und Zeilenformat-Fälle in
      `tests/test_providers_multi.py`.
- [ ] P3: Volume-Label-Matching per Substring ("Google Drive"/"pCloud" in
      label; providers.py:208/402) — umbenannte Volumes werden fehlklassifiziert.
      Exakteres Matching NUR mit realen Labels beider Clients verifizieren
      (pCloud-Label könnte "pCloud Drive" sein — exakter Vergleich bräche das).
- [x] P3: failed-Tasks (neu seit Retry-Cap 2026-07-12) tauchen im Tray-Status
      nirgends auf (models.status_counts zählt sie nicht) — UI-Sichtbarkeit
      ergänzen (Zähler oder Menüpunkt "Fehlgeschlagene anzeigen/aufräumen"). -- DONE 2026-07-12 (Statuszähler für permanent fehlgeschlagene Tasks in Tray/CLI ergänzt)

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
- [x] Projekt-Testzahl und Cross-Platform-Status in README/`llms.txt`/Roadmap
      auf den echten lokalen Stand ziehen. -- DONE 2026-07-17
      `PYTHONPATH=src python -m pytest -q` lieferte am 2026-07-17 noch 157/157 grün; README,
      README.de, `llms.txt`, ROADMAP und CHANGELOG sind daran synchronisiert.
      Neuer Guard `tests/test_docs_contract.py` hält Releaseversion und
      dokumentierte Testzahl gegen Paketstand bzw. gesammelte Pytest-Suite fest.
- [x] Cross-Platform: Plattform-Pfade für `data_dir()` -- DONE 2026-07-14
      `paths.data_dir()` nutzt jetzt `%LOCALAPPDATA%\CloudLockFixer` unter
      Windows, `~/Library/Application Support/CloudLockFixer` unter macOS und
      `$XDG_DATA_HOME/cloudlockfixer` bzw. `~/.local/share/cloudlockfixer` unter
      Linux. Regressionen: `tests/test_paths_cross_platform.py`.
- [x] Cross-Platform: Linux-XDG-Autostart -- DONE 2026-07-18
      `$XDG_CONFIG_HOME/autostart/cloudlockfixer.desktop` (Fallback: `~/.config`)
      wird atomar angelegt, gegen den aktuellen Startbefehl geprüft und idempotent
      entfernt. Vier Vertrags-Tests plus Linux-Source-Smoke und echter Ubuntu-/WSL-
      Roundtrip sind grün; native Linux-Pakete bleiben späterer Release-Scope.
- [x] Cross-Platform: Linux-Support (siehe PORTIERUNGSPLAN.md) -- DONE 2026-07-06
      Lokaler Source-Support ist über `tests/source_platform_smoke.py` und die
      GitHub-Actions-Matrix `ubuntu-latest` abgesichert; native Linux-Pakete
      bleiben späterer Release-Scope.
- [x] Cross-Platform: macOS-Support (siehe PORTIERUNGSPLAN.md) -- DONE 2026-07-06
      Lokaler Source-Support ist über `tests/source_platform_smoke.py` und die
      GitHub-Actions-Matrix `macos-latest` abgesichert; `.app`-/DMG-Paketierung
      bleibt späterer Release-Scope.
- [x] Weitere Provider: Box, Nextcloud, pCloud, Synology Drive
      Box erledigt 2026-06-17 (`~/Box` plus `CustomBoxLocation`-Registry-Pfad, `Box.exe`-Prozesssteuerung).
      Nextcloud erledigt 2026-06-16 (`nextcloud.cfg`-Root-Erkennung + Prozesssteuerung).
      pCloud erledigt 2026-06-28 (Volume-Label-Scan via `GetVolumeInformationW`, `virtual` mount, `pCloud.exe`-Prozesssteuerung, 9 Tests).
      Synology Drive erledigt 2026-06-30 (`~/SynologyDrive`-Default-Root, `cloud-drive-ui.exe`-Prozessprüfung/-Resume, 6 Tests).


## TASKPLAN-FORMALISIERUNG — 2026-07-16

Exit-0-Deep-Bündel des TASKWRITER-Selektors für CODING/REL-PUB_CloudLockFixer. Zehn Aufgaben formalisiert, nicht umgesetzt; Produktdateien, Tests und Builds blieben unverändert.

- TASKPLAN #852 / TW-CLF-01 — Versions- und Release-Stand konsolidieren
- TASKPLAN #853 / TW-CLF-02 — Testnachweis und Cross-Platform-Status synchronisieren
- TASKPLAN #854 / TW-CLF-03 — Design-, Roadmap- und Sicherheitsvertrag angleichen
- TASKPLAN #855 / TW-CLF-04 — Synology-Pause/Resume auf echtem Windows-Prozessmodell verifizieren
- TASKPLAN #856 / TW-CLF-05 — Volume-Label-Erkennung gegen reale Windows-Labels härten
- TASKPLAN #857 / TW-CLF-06 — Copy-Verifikation vor destruktivem Delete absichern
- TASKPLAN #858 / TW-CLF-07 — Touch-based-Migration nach Plan D vorbereiten
- TASKPLAN #859 / TW-CLF-08 — Build-, Dependency- und CI-Vertrag schließen
- TASKPLAN #860 / TW-CLF-09 — Frühes Runtime-Logging und Debug-Pfad absichern
- TASKPLAN #861 / TW-CLF-10 — Windows-Release-Smoke für Sicherheitsgrenzen formalisieren

Belegte Ist-Stände: Source und neuester Release-Tag stehen lokal auf 0.2.2,
während Root-Registry/GitHub-Status noch 1.0.0 führen; `PYTHONPATH=src python -m
pytest -q` liefert lokal 161 gesammelte Tests und ist in README/`llms.txt`/
CHANGELOG nachgezogen; Cross-Platform-Source-Support sowie Linux-XDG-Autostart
sind in der Roadmap explizit als erledigte Source-/CI-Stände markiert. Offen
bleiben Synology-, Volume-Label-,
Copy-Integritäts-, Plan-D-, Build-/CI-, Startdiagnose- und Windows-Smoke-Gates
sowie die separate Root-Release-Entscheidung.
