# CloudLockFixer — Web Companion & PWA

**Stand:** 2026-10-30  
**Version:** 1.0.0  
**Architektur:** Local-First / Zero-Egress Progressive Web App (PWA)  

---

## Zweck

Der **CloudLockFixer Web Companion** ist eine autarke, schreibgeschützte Web-Anwendung zur Inspektion von CloudLockFixer-Zuständen auf mobilen Endgeräten (Smartphones, Tablets), Zweitrechnern oder im Desktop-Browser.

### Kernfunktionen
- **Local-First & Zero-Egress:** Keine externen CDNs, kein Tracking, kein Upload zu Drittservern. Alle Daten verbleiben vollständig im Browser.
- **Offline PWA:** Installierbar auf Android, iOS, Windows und macOS via W3C WebManifest (`manifest.json`) und Cache-First Service Worker (`sw.js`).
- **Dashboard & KPIs:** Übersicht über Gesamtaufgaben, offene/fällige Operationen, verzögerte Aufgaben im exponentiellen Backoff, Fehlversuche und aktive Sync-Provider.
- **Queue-Monitor:** Durchsuchbare und filterbare Tabelle aller Aufgaben mit ID, Operation, Pfad, Status, Wiederholungszählern und nächstem Ausführungszeitpunkt.
- **Sync-Provider-Status:** Kacheln für alle erkannten Cloud-Synchronisationsdienste (OneDrive, Google Drive, Dropbox, Box, Nextcloud, pCloud, Synology Drive, iCloud) mit Prozess-Status und Mount-Typ.
- **Tier-2 Mehrsprachigkeit:** Vollständige Benutzeroberfläche in 6 Sprachen (`de`, `en`, `es`, `zh`, `ja`, `ru`).
- **Dark/Light Theme:** Barrierefreie Umschaltung mit 44px Mindest-Touch-Targets.

---

## Verwendung

1. **Snapshot exportieren:**
   Auf dem Desktop-Rechner mit CloudLockFixer:
   ```bash
   clf export-snapshot --pretty
   ```
   oder über das Tray-Menü: **Snapshot exportieren...**
   Die Datei `cloudlockfixer-snapshot-v1.json` wird erzeugt.

2. **Web Companion öffnen:**
   Öffne `web_companion/index.html` in einem beliebigen modernen Webbrowser (Chrome, Safari, Firefox, Edge).

3. **Snapshot laden:**
   Ziehe die Datei per Drag & Drop in die Ablagezone oder klicke auf **Snapshot laden**. Alternativ kann über **Demo-Snapshot** ein synthetischer Datensatz zur Demonstration geladen werden.
