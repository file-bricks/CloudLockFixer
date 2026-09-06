# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke finden, melden Sie diese bitte verantwortungsvoll:

1. **Kein öffentliches Issue eröffnen**
2. **GitHub Private Vulnerability Reporting verwenden:** [GitHub Security Advisories](https://github.com/file-bricks/CloudLockFixer/security/advisories/new)
3. Beschreibung, Reproduktionsschritte und potenzielle Auswirkungen angeben

### So melden Sie ein Problem

1. Öffnen Sie im Repository: `Security` → `Advisories` → `New`
2. Tragen Sie Titel, Beschreibung, Schweregrad und betroffene Versionen ein
3. Reichen Sie die Meldung privat ein
4. Alternativ können Sie Sicherheitsbedenken per E-Mail an `security@ellmos.ai`, `lukas@open-bricks.org`, `support@lukasgeiger.com` oder `info@file-bricks.org` senden.

### Unterstützte Versionen / Supported Versions

| Version | Unterstützt | Anmerkung |
|---------|-------------|-----------|
| `0.2.x` | :white_check_mark: | Aktiver Entwicklungszweig / Active development |
| `< 0.2.0` | :x: | Veraltet / Unsupported |

### Sicherheits- & Datenschutzgarantien (Zero-Egress & Local-First)

- **100% Zero-Egress & Local-First:** CloudLockFixer enthält keinerlei Telemetrie, Analytics, Tracking oder Netzwerk-Sockets. Alle Operationen, Queues (`queue.txt`, `queue.json`) und Logs verbleiben ausschließlich lokal auf Ihrem System.
- **Unprivilegierter Modus (Least Privilege):** Die Anwendung erfordert und erbittet keine Administrator-/Root-Rechte. Autostart-Einträge und Explorer-Kontextmenüs werden strikt im Benutzerspeicher (`HKCU`, `~/.config/autostart`, `~/Library/LaunchAgents`) verwaltet.
- **Kryptografische Kopieverifikation:** Destruktive `move`- und `rename`-Operationen im `copy+delete`-Workaround führen vor dem Löschen der Originaldatei stets eine vollständige SHA-256-Streaming-Inhaltsprüfung durch.
- **Fail-Closed & Fehlertoleranz:** Bei Datei- oder Provider-Sperren bricht die Operationskette sicher ab, behält den Zustand zur späteren Wiederholung bei und verhindert Datenverlust.

### Geltungsbereich

CloudLockFixer führt verzögerte Dateisystem-Operationen aus und steuert
Sync-Clients. Sicherheitsrelevant sind insbesondere:

- Dateisystem-Operationen (umbenennen / verschieben / löschen via copy+delete mit SHA-256-Inhaltsdigest-Prüfung vor Quell-Löschungen)
- Steuerung von Sync-Clients (Prozess beenden/starten, z. B. `OneDrive.exe`, `SynologyDrive.exe`, `pCloud.exe`)
- Autostart-Mechanismen & System-Integration (Windows Registry `HKCU\...\Run`, Linux XDG `.config/autostart`, macOS LaunchAgent `~/Library/LaunchAgents`, Explorer-Kontextmenü)
- Verarbeitung der Queue-Eingaben (`queue.txt` / `queue.json`, CLI-Argumente und `&&`-Ketten)
- Retry-/Fehlerzustand: Retryfähige Tasks bleiben standardmäßig pending und
  werden nicht allein wegen der Versuchszahl aufgegeben. Ein endliches Limit
  ist nur explizit pro Worker-Aufruf möglich.

### Reaktionszeit

Sicherheitsrelevante Meldungen werden innerhalb von 48 Stunden gesichtet und priorisiert behandelt. Bitte geben Sie ausreichend Zeit zur Behebung, bevor Sie Details öffentlich machen.

---

## English

### Reporting a Vulnerability

If you find a security vulnerability, please report it responsibly:

1. **Do not open a public issue**
2. **Use GitHub Private Vulnerability Reporting:** [GitHub Security Advisories](https://github.com/file-bricks/CloudLockFixer/security/advisories/new)
3. Include a description, reproduction steps, and potential impact

### How to Report

1. Open: `Security` → `Advisories` → `New`
2. Fill in the title, description, severity, and affected versions
3. Submit the report privately
4. Alternatively, email security concerns directly to `security@ellmos.ai`, `lukas@open-bricks.org`, `support@lukasgeiger.com`, or `info@file-bricks.org`.

### Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| `0.2.x` | :white_check_mark: | Active development branch |
| `< 0.2.0` | :x: | End of life / Unsupported |

### Security & Privacy Guarantees (Zero-Egress & Local-First)

- **100% Zero-Egress & Local-First:** CloudLockFixer contains zero telemetry, analytics, tracking, or network calls. All queues (`queue.txt`, `queue.json`) and logs remain strictly on your local machine.
- **Unprivileged Execution (Least Privilege):** The application runs entirely in user space without requiring administrator / root elevation. Autostart and context menu integrations are confined to user scopes (`HKCU`, `~/.config/autostart`, `~/Library/LaunchAgents`).
- **Cryptographic Verification:** Destructive fallback `move` and `rename` operations compute and verify full streaming SHA-256 payload digests prior to deleting the source files.
- **Fail-Closed Safety Bounds:** When locks or filesystem conflicts occur, execution chains halt safely, preserving pending state for later retries without data loss.

### Scope

CloudLockFixer performs delayed file system operations and controls sync
clients. Security-relevant areas include:

- File system operations (rename / move / delete via copy+delete with SHA-256 payload digest verification before source deletion)
- Sync-client control (terminating/starting processes, e.g. `OneDrive.exe`, `SynologyDrive.exe`, `pCloud.exe`)
- Autostart mechanisms & system integration (Windows Registry `HKCU\...\Run`, Linux XDG `.config/autostart`, macOS LaunchAgent `~/Library/LaunchAgents`, Explorer context menu)
- Processing of queue input (`queue.txt` / `queue.json`, CLI arguments and `&&` chains)
- Retry/error state: retryable tasks remain pending by default and are not
  abandoned solely by attempt count. A finite limit is available only as an
  explicit worker-call option.

### Response Time

Security-relevant reports are acknowledged within 48 hours and prioritized for rapid resolution. Please allow reasonable time before public disclosure.
