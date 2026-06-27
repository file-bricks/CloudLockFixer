# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- **Box provider (Windows):** root auto-discovery via `~/Box` plus optional `CustomBoxLocation` registry path, process detection via `Box.exe`, and pause/resume support.
- **Nextcloud provider (Windows):** root auto-discovery via `%APPDATA%\\Nextcloud\\nextcloud.cfg` plus default `~/Nextcloud`, process detection via `nextcloud.exe`, and pause/resume support.
- README.md, README.de.md and `llms.txt`: added discovery/search context for
  OneDrive access-denied, `cldflt.sys`, Windows Cloud Files filter, error
  `0x8007016A`, and cloud-sync locked-folder retry workflows.

### Behoben / Fixed
- **Tray task dialog now supports files as well as folders:** the GUI no longer
  forces source selection through a folder-only picker, so delayed rename/move/delete
  actions cover the same file/folder scope that the product documentation promises.
- **Autostart in packaged builds:** PyInstaller/Frozen builds now register the
  packaged executable instead of the source-tree `clf_launcher.pyw`.
- `tests/source_platform_smoke.py`: headless Smoke-Tests für Linux und macOS — prüft Modul-Import, Version, `ops`-Operationen (rename/move/delete), `models.Queue`-Persistenz, `paths.data_dir()` und `worker.run_once()` ohne Cloud-Client oder GUI.
- `.github/workflows/source-platform-smoke.yml`: CI-Matrix für `ubuntu-latest` und `macos-latest`, die die Smoke-Tests bei jedem Push/PR auf `main` ausführt.

### Behoben / Fixed
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
