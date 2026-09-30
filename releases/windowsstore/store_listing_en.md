# Store Listing (English) — CloudLockFixer

### Short Description (max 100 chars)
Local Windows utility for delayed file operations in locked cloud synchronization folders.

### Description
CloudLockFixer is a lightweight, local desktop and system tray utility designed to resolve persistent file lock conflicts in cloud-synchronized folders. When active file handles prevent renaming, moving, or deleting items, CloudLockFixer enqueues the operations into a transparent local task list and executes them cleanly as soon as the file lock is released or by safely pausing the corresponding sync client temporarily.

**Key Features:**

- **Delayed File Operations:** Effortlessly rename, move, and delete files that are temporarily locked by active sync routines.
- **Transparent Task Queue:** All pending actions are organized in a local queue and processed periodically or on demand.
- **Safe Copy-and-Delete Fallback:** Cryptographic checksum verification ensures complete data integrity before any source file is deleted.
- **Intelligent Provider Detection:** Distinguishes between standard sync directories and virtual drive mounts to protect filesystem integrity.
- **Preventive File Watcher:** Monitors active directories during bursts of modifications to prevent lockups proactively.
- **Configurable Retry Limits:** Tailor retry policies and receive optional desktop toasts when permanent obstacles arise.
- **Bilingual Interface:** Native support for English and German with automatic system language detection.
- **Zero-Egress Privacy:** Operates entirely offline with no network connections, no telemetry, and no account requirements.

### Keywords
file lock, cloud sync, file unlocker, tray tool, task queue, background tool, file manager

### Category
Utilities
