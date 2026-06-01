# CloudLockFixer (CLF-WDAS)

> 🇩🇪 **Deutsche Version:** [README.de.md](README.de.md)

**CloudLockFixer** *with Delayed Action Service* is a Windows tray tool that
reliably performs file/folder operations (**rename / move / delete**) inside
cloud-sync folders — even while the Windows Cloud Files filter (`cldflt`) is
blocking them. You **queue an action** and it is carried out **"eventually,"
automatically** — fire & forget.

## Why?

`cldflt.sys` (installed by OneDrive, Dropbox, Google Drive, iCloud — anything
using the Cloud Files API) intercepts `rename()` at the driver level and
returns "Access denied"/EXDEV while it is active. The **Microsoft-recommended
workaround** is to replace `rename()` with **copy()+delete()** — which is
exactly what this tool does, plus delayed retries and optional pausing of the
sync client.

## Features

- Queue file/folder operations and let them run fire & forget
- `copy+delete` fallback that bypasses the `cldflt` lock automatically
- Chains of 1–4 steps with safe ordering — destructive steps run only after the
  preceding step succeeds (no data loss)
- Multiple input paths: **CLI** (for LLMs/scripts), human-readable
  **`queue.txt`**, **tray dialog**, and an **Explorer right-click** context menu
- Auto-retry on a configurable interval (default 2 h) and on demand
- Optional sync-client pause/restart during an operation (OneDrive provider)
- Optional preventive watcher that pauses/resumes the sync client based on
  folder activity
- Autostart with Windows; single-instance tray app

## Installation

### Requirements
- Windows (the `cldflt` filter is Windows-specific)
- Python 3.10+
- PySide6 (>= 6.7)

### Steps
1. Clone the repository
2. `pip install -r requirements.txt`
3. Start the tray app: double-click `START.bat`, or
   `PYTHONPATH=src python -m cloudlockfixer`

## Usage

### Tray app
Starts with Windows when autostart is enabled. Tray menu: *Add task…*,
*Run now* (also *with OneDrive pause*), *Interval* (30-min steps, default 2 h),
*Start with Windows*, *Open queue/log*.

### CLI (for LLMs/scripts)
```
clf add --rename "C:\...\OldFolder" "NewName"
clf add --move   "C:\local\x"        "C:\onedrive\x"
clf add --delete "C:\onedrive\old"
clf add --chain  'move "C:\local\x" "C:\onedrive\x" && delete "C:\onedrive\old"'
clf list
clf run-now [--pause]
```
(dev invocation: `PYTHONPATH=src python -m cloudlockfixer.cli ...`)

### queue.txt (human/LLM)
A file at `%LOCALAPPDATA%\CloudLockFixer\queue.txt`, one line per task
(`rename` / `move` / `delete`, chaining with `&&`). Consumed lines are
automatically commented out with `#>`.

## How it works

- **Chains (1–4 steps):** step N runs only after step N-1 succeeds. A
  destructive `delete` runs only after its preceding step succeeded → no data
  loss.
- **copy+delete primitive:** an in-place attempt is made first; on a lock it
  automatically falls back to copy → verify → delete. Idempotent (safe to
  retry).
- **Worker:** runs on start + every 2 h (configurable) + on demand. If a task
  is stuck repeatedly, the responsible sync client is paused for that run and
  restarted afterwards.

## Status / Roadmap

- **P1 (done):** Core (copy+delete, chains, retry) · CLI · `queue.txt` · Tray ·
  Autostart · OneDrive provider.
- **P2 (done):** Explorer right-click context menu (HKCU cascade, opt-in via
  tray toggle).
- **P3 (done):** Preventive watcher (observes the change rate of *configured*
  folders → pauses/resumes the sync client; bounded, stat-only, does not
  hydrate online-only placeholders; opt-in).
- **Tests:** `pytest`, 49 passing (core + P2/P3 + i18n + multicloud regressions).
- **Open/future:** more provider adapters (Dropbox / Google Drive / iCloud);
  optional suppression of sync-client relaunch during long operations.

Windows-only; the core is platform-neutral for later ports.
Design notes: [`docs/DESIGN.md`](docs/DESIGN.md).

## License

MIT — see [LICENSE](LICENSE).

This project depends on **PySide6** (Qt for Python), licensed under the **LGPL
v3**. PySide6 is used as an unmodified third-party dependency.
