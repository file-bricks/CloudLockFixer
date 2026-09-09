# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Bugfix: Provider-Pfad-Sicherheit & Existenzprüfung (Bug #12-1) (2026-09-09)
- **Verhinderung relativer CWD-Pfade bei fehlendem APPDATA/LOCALAPPDATA (`providers.py`):** Behebung einer Schwachstelle (CWE-426 Untrusted Search Path), bei der nicht gesetzte Umgebungsvariablen `APPDATA`/`LOCALAPPDATA` zu relativen Pfaden führten und versehentlich Dateien im aktuellen Arbeitsverzeichnis als Provider-Konfigurationen geladen oder relative Binaries ausgeführt werden konnten.
- **Validierung und Filterung von Sync-Roots (`providers.py`):** `NextcloudProvider`, `DropboxProvider` und `OneDriveProvider` validieren nun gefundene Verzeichnisse strikt auf `p.is_absolute() and p.exists()`, um veraltete oder gelöschte Pfade nicht mehr als aktive Sync-Roots zu registrieren.
- **Regressionstest-Suite erweitert (`tests/test_bugsweep_regressions.py`):** 3 neue Regressionstests gegen relative CWD-Pfadübernahmen, nicht-existente Sync-Roots und relative Resume-Binaries verankert.
- The verification contract reflects the current unreleased source state: 240 passing tests.

### Plattform-Transfer: Provider-Abstraktion Linux & macOS (Phase 1) (2026-09-08)
- **Plattformübergreifende Prozessverwaltung (`providers.py`):** `_check_process()` und `_kill_process()` von reinem Windows-`tasklist`/`taskkill` auf Cross-Platform-Erkennung (`pgrep -f`, POSIX `/proc` Fallback, `pkill -f` mit Timeout und Verifikation) und Namens-Aliase für Linux/macOS umgestellt.
- **Provider-Erkennung auf macOS & Linux (`providers.py`):** Native Pfaderkennung für macOS (`~/Library/CloudStorage/` für OneDrive, Google Drive, Box, Dropbox; `~/Library/Mobile Documents/com~apple~CloudDocs` für iCloud; `~/Library/Preferences/Nextcloud/nextcloud.cfg` für Nextcloud; `~/Library/Application Support/` für Dropbox & Synology Drive) und Linux (`~/.config/Nextcloud/nextcloud.cfg`, `~/.dropbox/info.json`, `~/.SynologyDrive`, `~/pCloudDrive`) implementiert.
- **Plattformübergreifendes Resume:** Native Relaunch-Mechanismen für macOS (`open -a`) und Linux (Executable-Suche per `shutil.which`) für alle unterstützten Provider verankert.
- **Cross-Platform Vertragstests (`tests/test_providers_cross_platform.py` & `tests/source_platform_smoke.py`):** 17 neue Vertragstests für Prozessabstraktion, POSIX-Signalbehandlung, Pfad-Erkennung und Resume-Mechanismen implementiert.

### Standard-App-Icons, Multi-Layer ICO & Store-Readiness (2026-09-08)
- **Multi-Layer Windows-Icon & Desktop-Parität:** Hochauflösendes 7-Layer Windows ICO (`CloudLockFixer.ico`, `DesktopIcon.ico`, `resources/icon.ico`, `assets/icon.ico`) mit Standardauflösungen 16x16, 24x24, 32x32, 48x48, 64x64, 128x128 und 256x256 sowie Master-PNGs (1024x1024) in Root, `resources/` und `assets/` bereitgestellt.
- **PWA- & Mobile-Iconsuite (`mobile_icons/`):** Vollständige Mobile-/PWA-Icons (`icon-192.png`, `icon-512.png`, `icon-maskable-192.png`, `icon-maskable-512.png`, `apple-touch-icon.png`, `favicon.png`, `favicon.ico`) inklusive standardkonformer `manifest.json`.
- **Windows Store Readiness Assets (`store_assets/`):** Standardkachel- und Store-Icons (`icon_44x44.png`, `icon_50x50.png`, `icon_150x150.png`, `icon_310x150.png` [Breitkachel], `icon_310x310.png` [Großkachel]) nach Windows-Store-Spezifikation erzeugt.
- **Vertragstestsuite für Icons & Assets (`tests/test_assets_and_icons.py`):** 5 neue Vertragstests für Master-Icons, Multi-Layer-ICO-Parität, PWA-Manifest und Store-Asset-Dimensionen verankert.

### Sicherheits- & Lizenzaudit (Software Security & License Audit) (2026-09-08)
- **Abhängigkeits-Schwellenwerte gehärtet (Vulnerability Floors):** Build-Abhängigkeit `Pillow` auf `>=12.3.0` angehoben (behebt 26 bekannte Sicherheitslücken in <=12.2.0, u. a. OS Command Injection via `WindowsViewer.get_command()` GHSA-4x4j-2g7c-83w6 und Decompression-Bomb-Bypass GHSA-45hq-cxwh-f6vc). `PySide6` auf `>=6.7.0` vereinheitlicht. `pyproject.toml` um `[project.optional-dependencies]` für `test` (`pytest>=9.1.1` gegen CVE-2025-7117 / GHSA-6w46-j5rx-g56g), `lint` (`ruff>=0.9.0`) und `build` (`PyInstaller>=6.0`, `Pillow>=12.3.0`) ergänzt.
- **Vollständiges Drittanbieter-Lizenzinventar (`THIRD_PARTY_LICENSES.txt`):** Drittanbieter-Inventar von 4 Zeilen auf alle direkten und transitiven Laufzeit-, Build-, Test- und Lint-Abhängigkeiten (`PySide6`, `shiboken6`, `PyInstaller`, `Pillow`, `altgraph`, `pyinstaller-hooks-contrib`, `packaging`, `pytest`, `pluggy`, `iniconfig`, `ruff`) erweitert, inklusive Upstream-URLs, Lizenztyp und MIT-Gültigkeitsgrenzen (LGPL-3.0 dynamische Bindung, PyInstaller Special Exception).
- **Härtung der Versionskontrolle (`.gitignore`):** Cloud-Sync-Konfliktkopienmuster (`*-WORKSTATION-LG*`, `*-ASUS-GEI*`, `*.conflict`, `*.sync-conflict-*`) explizit in `.gitignore` verankert.
- **Sicherheits- & Lizenzvertrags-Testsuite (`tests/test_security_license_contract.py`):** 6 neue Vertragstests für Schwachstellenschwellenwerte, Lizenzvollständigkeit, `.gitignore`-Muster, Ausschluss von Hardcoded-Entwicklerpfaden/Secrets, Zero-Egress-Offline-Hermetizität und zweisprachige 48h-SLA-Sicherheitsrichtlinie.

### Marketing, Design & Auffindbarkeit (Pfad B) (2026-09-06)
- **Interaktive Mermaid-Architektur- und Ablaufdiagramme:** Aufnahme zweier interaktiver Mermaid-Diagramme (`flowchart TD` für Ingestion-Kanäle, Queue-Orchestrierung, Cloud-Provider-Sensorik und Ausführung mit SHA-256-Kopieüberprüfung; `sequenceDiagram` für End-to-End-Tasklebenszyklus, Sperrerkennung und Fallback-Auflösung) in `README.md` und `README.de.md`.
- **Zweisprachige Schnellnavigation & Kernfähigkeiten-Tabelle:** 14-Punkte-Schnellnavigation mit Direktankern sowie tabellarische Übersicht der Kernfähigkeiten und Governance-/Sicherheitsgarantien (`copy+delete`-Fallback, atomare Mehrschrittketten, Multi-Cloud-Provider-Sensorik, Zero-Egress, Least Privilege und idempotente Retry-Engine).
- **Geschwister-Ökosystem-Matrix:** Verknüpfungsmatrix zu Partner-Repositories innerhalb von `file-bricks`, `open-bricks`, `ellmos-ai`, `dev-bricks` und `doc-bricks`.
- **Sicherheitsrichtlinie & Unterstützte Versionen:** Aufnahme der formalen Versionstabelle (`0.2.x`, `< 0.2.0`) in `SECURITY.md` in Deutsch und Englisch.
- **Metadaten- & Vertragstestsuite erweitert:** 4 neue Vertragstests in `tests/test_metadata.py` für Mermaid-Diagramme, Geschwister-Ökosystem, Schnellnavigation und Versionstabelle.
- The verification contract reflects the current unreleased source state: 215 passing tests.

### Behoben / Fixed (2026-08-29)
- **Terminal fehlende Move-/Rename-Quellen:** Sicher fehlende aktuelle Quellen werden aus der Provider-Eskalation ausgeschlossen. Die normale Ausführung entscheidet danach race-sicher zwischen idempotentem Erfolg und terminaler Blockierung. Bestehende v1-Queues werden beim nächsten Lauf ohne Schemawechsel idempotent aktualisiert.
- **Provider-Eskalation:** Für die Pause werden nur noch Pfade des aktuell anstehenden Kettenschritts betrachtet. Erfolgreiche Move-/Delete-Abläufe und retryfähige Cloud-Sperren behalten ihr bisheriges Verhalten.

### Behoben / Fixed (Bugsweep 2026-08-24)
- **Case-Only Rename/Move auf case-insensitiven Dateisystemen (`ops.py`):** Behebung eines Fehlers, bei dem reine Groß-/Kleinschreibungsänderungen (z. B. `foo.txt` → `FOO.TXT` oder `dir` → `DIR`) auf NTFS/macOS fälschlich als `bereits am Ziel` bewertet wurden, ohne die Namensschreibweise auf dem Datenträger zu aktualisieren. `_do_move` unterscheidet nun echten Gleichstand von Case-Only-Umbenennungen und wendet die Umbenennung direkt via `os.replace` bzw. über einen zweistufigen Zwischenschritt an.
- **Regressionstestsuite (`tests/test_bugsweep_regressions.py`):** 6 neue Testfälle für Datei- und Ordner-Case-Renames, Direkt-Rename, Zwischenschritt-Fallback bei Locks, `same_case`-Idempotenz und Worker-Task-Abarbeitung hinzugefügt.
- Gesamte Testsuite auf **199 Tests** erweitert (100% grün).

### Technische Hygiene & CI-Härtung (Pfad A) (2026-08-24)
- **CI-Matrix & Concurrency-Härtung:** GitHub Actions CI-Workflows (`.github/workflows/tests.yml` und `.github/workflows/source-platform-smoke.yml`) um Concurrency-Steuerung (`cancel-in-progress: true`), standardisierte Actions (`actions/checkout@v4`, `actions/setup-python@v5`), Python 3.10-3.13 Matrix und `ruff check .` Lint-Gate erweitert.
- **PEP 621 Standard Classifiers & URLs:** `pyproject.toml` um standardisierte Keywords, `[tool.ruff.lint]` und vollständige `[project.urls]` (Homepage, Documentation, Repository, Bug Tracker, Changelog, Security Policy, Parent Org, Umbrella Ecosystem) gehärtet.
- **Sicherheitsrichtlinie (SECURITY.md):** Doppelten Header-Block bereinigt, direkten Dachverband-Sicherheitskontakt `lukas@open-bricks.org` neben `security@ellmos.ai`, `support@lukasgeiger.com` und `info@file-bricks.org` verankert, direkten GitHub Security Advisories Link ergänzt und Zero-Egress-/Local-First-Invarianten bekräftigt.
- **Automatisierte Metadaten- & Invarianten-Vertragstestsuite:** Neue Testsuite in `tests/test_metadata.py` mit 8 Contract-Tests implementiert (PEP 621 Metadaten, URLs, Sicherheitsrichtlinie, CI Matrix & Concurrency, Zero-Egress/Offline Standardbibliotheks-Hermetizität, zweisprachige README-Parität, llms.txt Integrität, Versions-Parität).
- **Badges & Doku-Synchronisation:** `README.md`, `README.de.md` und `llms.txt` auf Python 3.10-3.13, CI-Status, Security-Policy und 199 verifizierte Tests synchronisiert.
- 199/199 verifizierte Pytest-Tests (100% grün).

### Hinzugefügt / Added
- **Task-Wiederaufnahme & Retry-Steuerung (P1):** Neue CLI-Befehle `clf retry <id>`
  und `clf retry-all` zur atomaren Wiederaufnahme fehlgeschlagener (`failed`) oder
  blockierter (`blocked`) Aufgaben zurück in den `pending`-Zustand (`retry_count = 0`,
  `last_outcome = "retryable"`). Partieller Fortschritt (`step_index`, `Step.copied`)
  und Fehlerprotokolle bleiben erhalten.
- **Wiederaufnahme-Aktion im Tray:** Kontextsensitive Menüaktion („Fehlgeschlagene wiederholen“ /
  „Retry failed tasks“) mit Zähler-Anzeige im Tray-Menü, die bei fehlgeschlagenen Tasks
  aktiviert wird und per Klick die Queue reaktiviert und sofort ausführt.
- **Queue-Methoden `retry_task()` und `retry_all()`:** Atomare, thread-sichere Methoden in
  `src/cloudlockfixer/models.py` für die gezielte und gesammelte Wiederaufnahme.
- **Tier-2 I18N-Expansion (Policy P-006):** Vollständige Unterstützung für 6 Sprachen
  (Deutsch `de`, Englisch `en`, Spanisch `es`, Chinesisch `zh`, Japanisch `ja`,
  Russisch `ru`) über alle 78 Übersetzungsschlüssel im strukturierten Dict-Katalog
  in `src/cloudlockfixer/i18n.py`.
- Erweiterte Spracherkennung in `i18n.detect_language()` und `settings.resolve_language()`
  für `es`, `zh`, `ja` und `ru`.
- Neues Sprachauswahl-Menü in `src/cloudlockfixer/tray.py` mit direkter Umschaltung
  aller 6 Sprachen inklusive Neustart-Hinweis.
- **Synology Drive & Daemon-Fallback:** `SynologyDriveProvider.resume()` startet nun
  auch `SynologyDrive.exe` als Fallback, falls die `cloud-drive-ui.exe`-GUI nicht
  vorhanden ist.

### Hinzugefügt / Added
- PEP 621 `pyproject.toml` mit Paketmetadaten, Pytest-Konfiguration und CLI-Entrypoint.
- Shields.io Badges (Tests, Python-Versionen, Lizenz, LLM-Ready) und LLM-Integrationshinweis in `README.md`.

### Geändert / Changed
- Worker-Ausgänge sind jetzt persistiert als `done`, `retryable`, `blocked`
  oder `permanent`. Ein bestehendes Ziel wird als sichtbarer `blocked`-Konflikt
  behandelt; nachweislich fehlende Move-/Rename-Quellen ohne vorhandenes Ziel
  werden terminal blockiert.
- Copy+delete-Retries behandeln eine bereits vollständig vorhandene Zielkopie
  nicht mehr als Zielkonflikt, falls das `copied`-Flag vor der Persistenz
  verloren ging; die Quelle wird dann idempotent entfernt.
- ROADMAP und TASKPLAN-Readback auf den verifizierten Retry-Vertrag (unbegrenzter
  Standard, 168 Tests) korrigiert.
- Retryfähige Aufgaben bleiben standardmäßig unbegrenzt `pending`, statt nach
  fünf Versuchen als dauerhaft fehlgeschlagen verworfen zu werden. Ein
  endliches Limit bleibt als expliziter Worker-Parameter verfügbar; eine
  Regression deckt mindestens sechs Fehlversuche ab.
- Volume-Label-Erkennung für Google Drive und pCloud verwendet nun eine
  normalisierte Exakt-Allowlist statt einer unsicheren Teilstring-Suche; frei
  umbenannte Laufwerke werden dadurch nicht als Cloud-Mount fehlklassifiziert.
- `RELEASE_GATE.md` hält die kanonische Source-Version 0.2.2, den historischen
  v1.0.0-Tag und die offenen Windows-/Security-Gates getrennt fest.
- `llms.txt` mit `Last-checked: 2026-08-24` Header versehen.
- Technische Hygiene & Doku-Wartung (Pfad A): 193/193 Pytest-Tests verifiziert und `llms.txt` Verification Timestamp auf 2026-08-24 aktualisiert.
- Development now follows Plan D: the verified Git working tree lives outside
  OneDrive, while OneDrive keeps the project pointer and documentation. GitHub
  remains the canonical code and synchronization source.
- `llms.txt` now reflects the current unreleased source state: 199 passing
  tests, the cross-platform data directory and Linux/macOS autostart contracts,
  the source-platform smoke test entry point, and the expanded provider set
  through Box, Nextcloud, pCloud and Synology Drive.
- Tray wording now says `Open data folder` / `Datenordner öffnen` instead of
  `Open queue/log`, because the action opens the local app folder with
  `queue.txt` and log files rather than a dedicated queue/log view.
- README.md, README.de.md and the roadmap/TODO notes now use the live 199-test
  suite count and distinguish packaged Windows scope from Linux/macOS source
  support and the implemented Linux XDG/macOS LaunchAgent integrations.

### Hinzugefügt / Added
- **macOS LaunchAgent autostart:** `autostart.py` now atomically writes,
  validates, refreshes and removes
  `~/Library/LaunchAgents/com.cloudlockfixer.agent.plist`. `plistlib` preserves
  argument boundaries and XML escaping. Three focused contracts plus the
  `macos-latest` source-platform smoke cover roundtrip, stale/malformed plist
  repair and paths with spaces or XML metacharacters. This is source-level
  evidence; a real Mac login/launchctl and GUI/cloud-client run remain open.
- **Linux XDG autostart:** `autostart.py` now writes, validates, refreshes and
  removes `cloudlockfixer.desktop` below `$XDG_CONFIG_HOME/autostart` (or
  `~/.config/autostart`) with an escaped `Exec` command and atomic replacement.
  Three focused contracts plus the Linux source-platform smoke cover roundtrip,
  stale-entry refresh and escaping; a real Ubuntu/WSL roundtrip also passed.
- `tests/test_docs_contract.py` verifies that `llms.txt` keeps the release
  version in sync with `cloudlockfixer.__version__` and that the published test
  count in the README files, `llms.txt` and `CHANGELOG.md` matches the actual
  collected pytest suite size.
- **Cross-platform data directory abstraction:** `paths.data_dir()` now uses
  the Windows `%LOCALAPPDATA%\CloudLockFixer` location, macOS
  `~/Library/Application Support/CloudLockFixer`, and Linux
  `$XDG_DATA_HOME/cloudlockfixer` with `~/.local/share/cloudlockfixer` fallback.
  Five focused path tests cover the platform branches without target hardware.
- **Cross-platform source support revalidated:** Linux/macOS source support is
  now treated as done at source-smoke level, backed by
  `tests/source_platform_smoke.py`, the existing GitHub Actions matrix for
  `ubuntu-latest` and `macos-latest`, and a fresh local 76-test verification.
  Native packages and real target-platform integration remain release scope.
- **Synology Drive provider (Windows):** root auto-discovery via the official
  default sync folder `~/SynologyDrive`, process detection via
  `cloud-drive-ui.exe`, and resume support via the local
  `%LOCALAPPDATA%\\SynologyDrive\\SynologyDrive.app\\bin\\cloud-drive-ui.exe`
  installation path. Covered by focused provider discovery, routing and resume
  tests.
- **Synology custom sync roots (Windows):** `SynologyDriveProvider` now scans
  local Synology app-data config files (`*.json` / `*.conf` / `*.cfg`) for
  `local_path` / `localPath` entries and accepts existing custom sync folders
  in addition to the default `~/SynologyDrive` root. Covered by focused JSON-
  and line-format provider tests.
- **pCloud provider (Windows):** `PCloudProvider` erkennt pCloud Drive als virtuellen
  Laufwerks-Mount (`mount_type="virtual"`) per `GetVolumeInformationW`-Volume-Label-Scan
  (Label muss "pCloud" enthalten). Prozesssteuerung via `pCloud.exe`; Resume sucht in
  `%LOCALAPPDATA%\Programs\pCloud\`, `C:\Program Files\pCloud\` und
  `C:\Program Files (x86)\pCloud\`. Da `mount_type="virtual"`, wird der Provider
  korrekt vom Pause-Guard ausgeschlossen. 9 neue Tests in `test_providers_multi.py`.
- **Box provider (Windows):** root auto-discovery via `~/Box` plus optional `CustomBoxLocation` registry path, process detection via `Box.exe`, and pause/resume support.
- **Nextcloud provider (Windows):** root auto-discovery via `%APPDATA%\\Nextcloud\\nextcloud.cfg` plus default `~/Nextcloud`, process detection via `nextcloud.exe`, and pause/resume support.
- README.md, README.de.md and `llms.txt`: added discovery/search context for
  OneDrive access-denied, `cldflt.sys`, Windows Cloud Files filter, error
  `0x8007016A`, and cloud-sync locked-folder retry workflows.

### Behoben / Fixed
- **Sichere Einzelwiederholung:** `clf retry <id>` lehnt nun erledigte und bereits
  laufende Aufgaben ab, statt sie still wieder in die Queue zu stellen. Die CLI
  nennt den aktuellen Status, sodass ausschließlich fehlgeschlagene oder blockierte
  Aufgaben wiederholt werden können.
- **Tray-Einstellungsfehler sind erklärt:** Wenn Windows Autostart oder das
  Explorer-Kontextmenü nicht anlegen beziehungsweise entfernen kann, setzt die
  App das Häkchen weiterhin auf den tatsächlichen Zustand zurück und zeigt nun
  zusätzlich eine fokussierbare, lokalisierte Fehlermeldung. Ein
  Regressionstest deckt beide abgewiesenen Umschalter ab.
- **Failed-Tasks sind im Status sichtbar:** Tasks, die nach dem Retry-Cap auf
  `status="failed"` stehen, werden jetzt von `models.status_counts()` separat
  gezählt und bleiben dadurch im Tray-Status sowie in der CLI-Run-Zusammenfassung
  sichtbar, statt bei leerer Pending-Queue als "keine offenen Aufgaben" zu
  verschwinden. 3 neue Regressionstests decken Counter, Tray-Status und
  i18n-Formatierung ab.
- **Review-Fixes (2026-07-12):**
  - **Virtual-Mount-Guard im Präventiv-Wächter:** `PreventiveWatcher.tick()`
    pausiert virtuelle Provider (Google Drive, pCloud) nie mehr; `tray.py`
    registriert für sie gar keinen Wächter — sonst risse der Prozess-Kill den
    Laufwerks-Mount ab.
  - **Robuster Laufwerks-Scan:** `_get_volume_label()` umschließt die Abfrage mit
    `SetThreadErrorMode(SEM_FAILCRITICALERRORS)` (verhindert die blockierende
    „Kein Datenträger"-Dialogbox) und fragt via `GetDriveTypeW` nur `DRIVE_FIXED`
    und `DRIVE_REMOTE` ab — Wechseldatenträger/CD-ROMs werden übersprungen.
  - **Retry-Cap statt Endlos-Retry:** dauerhaft scheiternde Tasks werden nach
    `DEFAULT_MAX_RETRIES` (5) auf `status="failed"` gesetzt (mit aussagekräftiger
    Fehlermeldung, i18n de/en) und nicht mehr aufgegriffen.
  - **Watcher/Worker-Race behoben:** jede Provider-Instanz hat einen eigenen
    `threading.RLock`, der `pause()`/`resume()` zwischen Wächter- und
    Worker-Thread serialisiert (kein globales Lock; Parallelität verschiedener
    Provider bleibt erhalten).
  - README/README.de: Provider-Liste um pCloud + Synology Drive ergänzt,
    Testzahl auf 144 aktualisiert. 12 neue Regressionstests in
    `tests/test_review_fixes_2026_07_12.py`.
- **Tray task dialog now supports files as well as folders:** the GUI no longer
  forces source selection through a folder-only picker, so delayed rename/move/delete
  actions cover the same file/folder scope that the product documentation promises.
- **Autostart in packaged builds:** PyInstaller/Frozen builds now register the
  packaged executable instead of the source-tree `clf_launcher.pyw`.
- `tests/source_platform_smoke.py`: headless Smoke-Tests für Linux und macOS — prüft Modul-Import, Version, `ops`-Operationen (rename/move/delete), `models.Queue`-Persistenz, `paths.data_dir()` und `worker.run_once()` ohne Cloud-Client oder GUI.
- `.github/workflows/source-platform-smoke.yml`: CI-Matrix für `ubuntu-latest` und `macos-latest`, die die Smoke-Tests bei jedem Push/PR auf `main` ausführt.

### Behoben / Fixed
- **Copy-Verifikation vor Löschen:** Der Copy+Delete-Fallback prüfte bislang nur
  Dateizahl und Gesamtgröße. Eine beschädigte Kopie mit identischer Größe konnte
  deshalb als vollständig gelten und das Löschen der Quelle freigeben.
  `_payload_signature()` berücksichtigt jetzt einen streamingfähigen SHA-256-
  Inhaltsdigest inklusive relativer Dateinamen; der Regressionstest deckt zwei
  gleich große Dateien mit abweichenden Bytes ab.
- **Bug #BW-1 — GoogleDriveProvider.resume() semantische Versionssortierung:**
  `sorted(glob("*/GoogleDriveFS.exe"), reverse=True)` nutzte lexikografische Sortierung;
  Versionsordner wie `"9.0.0"` rangierten dabei über `"62.0.1"` (`'9' > '6'`
  zeichenweise). Fix: neue Hilfsfunktion `_gdrive_version_key(p)` parst den
  Verzeichnisnamen als Integer-Tupel; `_RESUME_BASE` als Klassenattribut ermöglicht
  zudem sauberes Monkeypatching in Tests. Betrifft nur Installationen mit mehreren
  parallelen Google-Drive-Versionen (z. B. nach unvollständigem Update). Test:
  `test_googledrive_version_sort_key_is_semantic`, `test_googledrive_resume_picks_highest_semantic_version`.
- **Bug #BW-2 — PreventiveWatcher.tick() ignorierte resume()-Rückgabewert:**
  `self.provider.resume()` wurde ohne Prüfung des Rückgabewerts aufgerufen. Bei
  Fehlschlag (z. B. Prozess-Start verweigert) blieb `_paused_by_us=False` und
  `_last_activity=None` — der Watcher lief keinen neuen Cooldown, der Provider
  pausierte dauerhaft bis zum App-Neustart. Symmetrisch zum bereits in v0.2.2
  behobenen `pause()`-Bug. Fix: bei `resume() == False` werden `_paused_by_us=True`
  und `_last_activity=self._time()` wiederhergestellt, um nach dem nächsten
  Cooldown einen Retry zu ermöglichen. Test: `test_watcher_tick_retries_resume_after_failure`.
- **Robustheit #BW-R — _check_process() Groß-/Kleinschreibungsvergleich:**
  `exe_name in out` war case-sensitiv; Windows' `tasklist` gibt Prozessnamen in der
  tatsächlichen Binär-Schreibweise zurück (z. B. `Nextcloud.exe`, nicht
  `nextcloud.exe`). Fix: `exe_name.lower() in out.lower()`. Test:
  `test_check_process_case_insensitive_exe_name`.

### Behoben / Fixed
- **Bug 4 — falsches „completed" bei leerem Verzeichnis mit gesperrtem Eigen-Handle:**
  `_delete_dir_skip_locked()` meldete Erfolg anhand von `len(locked) == 0`. Ein
  LEERER Ordner, dessen eigenes Handle gesperrt ist (kein gesperrtes Kind, sondern
  der Ordner selbst — z. B. von `SearchIndexer.exe` gehalten), hat keine gesperrte
  Innendatei; das verschluckte `p.rmdir()`-`OSError` wurde so fälschlich als gelöscht
  gewertet. Folge: Der Worker markierte den Task „completed" und verwarf ihn, statt
  ihn erneut zu versuchen — der Ordner blieb für immer liegen. Fix: Erfolg wird jetzt
  am echten FS-Zustand gemessen (`not p.exists()`); `_delete_path()` liefert für den
  Eigen-Handle-Lock eine eigene Retry-Meldung. Tests: `TestEmptyDirOwnHandleLocked`
  (4 Tests). Ursache empirisch bestätigt (Windows Search Indexer, 2026-06-13).
- Guard in `_refresh_status()` against race between queue reload and worker thread.
- Thread-safe dict snapshot in `_watcher_tick` (tray).
- `tick_all()` helper extracted; real snapshot test added.

## [0.2.2] - 2026-06-06

### Behoben / Fixed
- Context menu command broken when app was installed from a PyInstaller `.exe`
  (resolved path used for registry key; now uses the correct exe path).
- `UnicodeDecodeError` in `_ingest_txt` now caught and skipped.
- `isinstance`-guard added for Dropbox section fields in provider detection.
- Unknown step fields in `Task.from_dict` are now filtered out silently.
- `ValueError` raised instead of `json.JSONDecodeError` for UTF-8-corrupted
  settings/models files.
- `pause()` return value now checked in watcher; `_paused_by_us` reset on failure.

## [0.2.1] - 2026-06-05

### Behoben / Fixed
- EBUSY-safe directory deletion and lock-error detection in `ops.py`.
- `is_installed()` now checks all `_BASES`, not only the first one — prevents
  false negatives when `BASES[0]` was removed but `BASES[1]` was still present.
- `--chain` now catches `ValueError` from `parse_txt_line` and returns exit code 2
  instead of an unhandled traceback.
- `DropboxProvider._detect_roots` guarded against non-dict JSON.
- `_ingest_txt` writes `queue.txt` atomically (tmp + replace).
- `Settings.load()` returns default when JSON root is not a dict.
- `Settings` write path uses atomic tmp-replace.
- Watcher timer now starts after the first watch-dir is added (tray fix).
- Double backslash in registry verb-key paths (context menu) corrected.
- `Queue.load` tolerates non-dict JSON root (prevents `AttributeError`).

## [0.2.0] - 2026-05-30

### Hinzugefügt / Added
- **Windows Multicloud Support:** Google Drive, Dropbox, and iCloud providers —
  auto-detection of roots, pause/resume support.
- **i18n support:** German and English UI, auto-detected from system locale.
- **GitHub Actions workflow** for Windows smoke tests on Python 3.10, 3.11, and 3.12.
- `llms.txt` with canonical machine-readable project context.
- `docs/DESIGN.md`, `ROADMAP.md`, `PORTIERUNGSPLAN.md`, `TODO.md`.
- Three core bug fixes after first real-world test: verify-cleanup,
  watcher-resume, queue-race.

### Geändert / Changed
- Locale detection no longer uses Python's deprecated `locale.getdefaultlocale()`.
- Roadmap and README updated to reflect current i18n and multicloud implementation.
- Tests: **88 passing** (core + P2/P3 + i18n + multicloud regressions).

## [1.0.0] - 2026-05-30

### Erstveröffentlichung / Initial release

- **Core:** Delayed file operations (rename / move / delete) with copy+delete as
  universal primitive, bypasses the Windows Cloud Files filter (`cldflt`). /
  Verzögerte Datei-Operationen mit copy+delete als Primitive.
- **Chains:** 1–4 steps per task; destructive steps only after preceding step
  succeeds (no data loss). / Ketten aus 1–4 Schritten; sicher geordnet.
- **Worker:** runs on start, periodically (default 2 h), and on demand, with retry.
- **CLI:** `clf add --rename|--move|--delete|--chain`, `list`, `run-now`.
- **queue.txt:** Human/LLM-readable input format.
- **Tray (PySide6):** task dialog, "Run now", interval, autostart.
- **OneDrive provider:** pause/restart sync client during operation.
- **Explorer context menu (P2):** delayed rename/move/delete, opt-in via tray toggle.
- **Preventive watcher (P3):** monitors change rate of configured folders and
  pauses/resumes the sync client (stat-only, opt-in).
- 17 passing tests.
