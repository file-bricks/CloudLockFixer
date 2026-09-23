# Store Listing - CloudLockFixer

## Deutsch

### Kurzbeschreibung (max 100 Zeichen)
Lokales Windows-Werkzeug zur verzögerten Ausführung von Dateisperren in Cloud-Sync-Ordnern.

### Beschreibung (max 10.000 Zeichen)
CloudLockFixer ist ein schlankes, lokales Desktop- und Tray-Werkzeug für Windows, das typische Dateisperren in Ordnern von Cloud-Synchronisationsdiensten auflöst. Wenn Dateien während des Abgleichs blockiert sind, reiht CloudLockFixer Umbenennungen, Verschiebungen oder Löschungen in eine transparente Warteschlange ein und führt sie zuverlässig aus, sobald die Sperre freigegeben ist oder durch gezieltes temporäres Pausieren des jeweiligen Clients gelöst werden kann.

**Hauptfunktionen:**

- **Verzögerte Dateioperationen:** Umbenennen, Verschieben und Löschen von Dateien ohne lästige Fehlermeldungen bei aktiven Dateisperren.
- **Transparente Warteschlange:** Alle ausstehenden Operationen werden lokal verwaltet und können auf Knopfdruck oder im konfigurierten Zeitintervall abgearbeitet werden.
- **Sicheres Copy-and-Delete-Verfahren:** Robuster Fallback mit kryptografischem Prüfsummen-Vergleich vor dem Entfernen der Quelldatei.
- **Intelligente Provider-Erkennung:** Automatische Unterscheidung zwischen synchronisierten Ordnern und virtuell gemounteten Laufwerken zum Schutz des Dateisystems.
- **Präventiver Wächter:** Überwacht Verzeichnisse bei hoher Änderungsrate und verhindert Sperren vorausschauend.
- **Konfigurierbare Wiederholungen:** Einstellbare Wiederholungszyklen und verlässliche Desktop-Benachrichtigungen bei dauerhaft blockierten Aufgaben.
- **Mehrsprachige Benutzeroberfläche:** Vollständige Unterstützung für Deutsch und Englisch mit automatischer Spracherkennung.
- **Zero-Egress & Datenschutz:** 100 % lokal ohne Internetverbindung, ohne Telemetrie und ohne Registrierungszwang.

**Warum CloudLockFixer?**

- Keine verlorenen Dateioperationen durch blockierte Cloud-Synchronisation
- Minimale Systembelastung durch ressourcenschonenden Hintergrundbetrieb im Infobereich
- Vollständige Kontrolle über alle Warteschlangen und Zeitpläne
- Keine Werbung, keine Abonnements und keine Cloud-Abhängigkeiten

### Schlüsselwörter
Dateisperre, Cloud-Sync, Warteschlange, Hintergrundtool, Datei-Entsperrer, Tray-Tool, Task-Manager

### Kategorie
Utilities

---

## English

### Short Description (max 100 chars)
Local Windows utility for delayed file operations in locked cloud synchronization folders.

### Description (max 10,000 chars)
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

**Why CloudLockFixer?**

- Eliminates frustrating "File in Use" errors in synchronized desktop directories
- Extremely lightweight background footprint in the Windows notification area
- Complete transparency with human-readable queues and detailed local diagnostics
- Open-source, local-first utility without ads, subscriptions, or remote dependencies

### Keywords
file lock, cloud sync, file unlocker, tray tool, task queue, background tool, file manager

### Category
Utilities
