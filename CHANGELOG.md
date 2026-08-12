# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- PEP 621 `pyproject.toml` mit Paketmetadaten, Pytest-Konfiguration und CLI-Entrypoint.
- Shields.io Badges (Tests, Python-Versionen, Lizenz, LLM-Ready) und LLM-Integrationshinweis in `README.md`.

### Geändert / Changed
- Retryfähige Aufgaben bleiben standardmäßig unbegrenzt `pending`, statt nach
  fünf Versuchen als dauerhaft fehlgeschlagen verworfen zu werden. Ein
  endliches Limit bleibt als expliziter Worker-Parameter verfügbar; eine
  Regression deckt mindestens sechs Fehlversuche ab.
- Volume-Label-Erkennung für Google Drive und pCloud verwendet nun eine
  normalisierte Exakt-Allowlist statt einer unsicheren Teilstring-Suche; frei
  umbenannte Laufwerke werden dadurch nicht als Cloud-Mount fehlklassifiziert.
- `RELEASE_GATE.md` hält die kanonische Source-Version 0.2.2, den historischen
  v1.0.0-Tag und die offenen Windows-/Security-Gates getrennt fest.
- `llms.txt` mit `Last-checked: 2026-07-26` Header versehen.
- Technische Hygiene & Doku-Wartung (Pfad A): 165/165 Pytest-Tests verifiziert und `llms.txt` Verification Timestamp auf 2026-07-26 aktualisiert.
- Development now follows Plan D: the verified Git working tree lives outside
  OneDrive, while OneDrive keeps the project pointer and documentation. GitHub
  remains the canonical code and synchronization source.
- `llms.txt` now reflects the current unreleased source state: 166 passing
  tests, the cross-platform data directory and Linux/macOS autostart contracts,
  the source-platform smoke test entry point, and the expanded provider set
  through Box, Nextcloud, pCloud and Synology Drive.
- Tray wording now says `Open data folder` / `Datenordner öffnen` instead of
  `Open queue/log`, because the action opens the local app folder with
  `queue.txt` and log files rather than a dedicated queue/log view.
- README.md, README.de.md and the roadmap/TODO notes now use the live 165-test
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
