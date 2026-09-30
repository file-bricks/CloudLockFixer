# Datenschutzerklärung / Privacy Policy

## Deutsch

CloudLockFixer ist ein lokales Desktop- und Hintergrundwerkzeug für Windows. Die Software verarbeitet Dateipfade, Warteschlangenaufträge und Einstellungen ausschließlich lokal auf dem System des Nutzers.

### Welche Daten CloudLockFixer verarbeitet

- Lokale Dateipfade, die vom Nutzer oder durch autorisierte Skripte in die Auftrags-Warteschlange (`queue.json` / `queue.txt`) eingetragen werden
- Einstellungen zur Ausführungshäufigkeit, Sprache, Wächterordnern und Wiederholungsversuchen (`settings.json`)
- Lokale Status- und Protokolldaten (`cloudlockfixer.log`) im anwendungseigenen Verzeichnis (`%LOCALAPPDATA%\CloudLockFixer`)

### Was CloudLockFixer nicht tut

- Keine Übertragung von Dateiinhalten oder Dateinamen an externe Server oder Dritte
- Keine Netzwerkverbindungen, kein Tracking, keine Telemetrie und keine Analysedienste (Zero-Egress)
- Kein Auslesen von persönlichen Kontodaten oder Passwörtern der installierten Cloud-Clients
- Keine Registrierung oder Kontoerstellung erforderlich

### Zugriff auf Dateisystem und Prozesse

CloudLockFixer greift auf lokale Dateipfade zu, um verzögerte Umbenennungen, Verschiebungen oder Löschungen auszuführen. Bei gesperrten Dateien kann die Software autorisierte lokale Sync-Client-Prozesse (z. B. OneDrive, Dropbox) temporär pausieren oder beenden und anschließend wieder starten, um blockierende Handles freizugeben.

### Speicherung und Bereinigung

Alle Konfigurationsdateien, Warteschlangen und Protokolldateien werden lokal im AppData-Verzeichnis gespeichert. Durch Deinstallation der Software oder Löschen des Datenordners können sämtliche gespeicherten Daten vollständig entfernt werden.

---

## English

CloudLockFixer is a local desktop and background utility for Windows. The software processes file paths, queued tasks, and configuration data strictly on the user's local machine.

### Data CloudLockFixer processes

- Local file paths submitted to the task queue (`queue.json` / `queue.txt`) by the user or local scripts
- Application settings including interval frequency, language, watch directories, and retry behavior (`settings.json`)
- Local log entries and diagnostic status (`cloudlockfixer.log`) within the application data folder (`%LOCALAPPDATA%\CloudLockFixer`)

### What CloudLockFixer does not do

- It does not transmit file contents, file names, or metadata to external servers or third parties
- It does not make outbound network connections, tracking calls, or telemetry transmissions (Zero-Egress)
- It does not collect user credentials, passwords, or personal account details from cloud sync clients
- It does not require online accounts or registration

### File system and process access

CloudLockFixer interacts with local files to complete delayed rename, move, or delete operations. When files are locked by active synchronization handles, the software may temporarily terminate or restart authorized local sync client processes (such as OneDrive or Dropbox) to release file handles safely.

### Storage and retention

All configuration files, queued tasks, and logs remain locally in the application data directory. Uninstalling the software or deleting the local data folder removes all associated local records completely.
