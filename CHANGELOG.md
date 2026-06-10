# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- `tests/source_platform_smoke.py`: headless Smoke-Tests für Linux und macOS — prüft Modul-Import, Version, `ops`-Operationen (rename/move/delete), `models.Queue`-Persistenz, `paths.data_dir()` und `worker.run_once()` ohne Cloud-Client oder GUI.
- `.github/workflows/source-platform-smoke.yml`: CI-Matrix für `ubuntu-latest` und `macos-latest`, die die Smoke-Tests bei jedem Push/PR auf `main` ausführt.

### Behoben / Fixed
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
