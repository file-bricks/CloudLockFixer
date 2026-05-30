# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke finden, melden Sie diese bitte verantwortungsvoll:

1. **Kein öffentliches Issue eröffnen**
2. **GitHub Private Vulnerability Reporting verwenden**
3. Beschreibung, Reproduktionsschritte und potenzielle Auswirkungen angeben

### So melden Sie ein Problem

1. Öffnen Sie im Repository: `Security` → `Advisories` → `New`
2. Tragen Sie Titel, Beschreibung, Schweregrad und betroffene Versionen ein
3. Reichen Sie die Meldung privat ein

Falls Private Vulnerability Reporting im Repository noch nicht aktiviert ist,
kontaktieren Sie die Maintainer direkt über GitHub und veröffentlichen Sie
keine Details in einem öffentlichen Issue.

### Geltungsbereich

CloudLockFixer führt destruktive Dateisystem-Operationen aus und steuert
Sync-Clients. Sicherheitsrelevant sind insbesondere:

- Dateisystem-Operationen (umbenennen / verschieben / löschen via copy+delete)
- Steuerung von Sync-Clients (Prozess beenden/starten, z. B. `OneDrive.exe`)
- Windows-Registry-Einträge (Autostart `HKCU\...\Run`, Explorer-Kontextmenü)
- Verarbeitung der Queue-Eingaben (`queue.txt` / `queue.json`, CLI-Argumente)

### Reaktionszeit

Bei kleineren Einzelprojekten können Reaktionszeiten variieren. Kritische
Probleme werden priorisiert. Bitte geben Sie ausreichend Zeit, bevor Sie
Details öffentlich machen.

---

## English

### Reporting a Vulnerability

If you find a security vulnerability, please report it responsibly:

1. **Do not open a public issue**
2. **Use GitHub Private Vulnerability Reporting**
3. Include a description, reproduction steps, and potential impact

### How to Report

1. Open: `Security` → `Advisories` → `New`
2. Fill in the title, description, severity, and affected versions
3. Submit the report privately

If private vulnerability reporting is not enabled yet, contact the maintainers
through GitHub and do not publish details in a public issue.

### Scope

CloudLockFixer performs destructive file system operations and controls sync
clients. Security-relevant areas include:

- File system operations (rename / move / delete via copy+delete)
- Sync-client control (terminating/starting processes, e.g. `OneDrive.exe`)
- Windows registry entries (autostart `HKCU\...\Run`, Explorer context menu)
- Processing of queue input (`queue.txt` / `queue.json`, CLI arguments)

### Response Time

For smaller solo projects, response times may vary. Critical issues will be
prioritized. Please allow reasonable time before public disclosure.
