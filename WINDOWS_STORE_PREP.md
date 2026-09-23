# Windows Store Preparation & Packaging Guide — CloudLockFixer

Stand: 2026-09-23

## Übersicht

CloudLockFixer wird als modernes MSIX-Paket für den Microsoft Store paketiert. Das Paket kapselt die lokale PySide6-Hintergrund- und Tray-Anwendung in einer sicheren Windows-Desktop-Bridge-Umgebung (`runFullTrust`).

## Metadaten & Identität

- **App Name:** CloudLockFixer
- **Publisher:** CN=52596601-BAB4-4F3F-B182-E8F3F273B202
- **Publisher Display:** Geiger
- **Identity Name:** Geiger.CloudLockFixer
- **Package Version:** 0.2.3.0
- **Category:** Utilities
- **Capabilities:** runFullTrust
- **Languages:** de-DE, en-US
- **Executable:** CloudLockFixer.exe

## Erledigte Vorbereitungsschritte

1. **Paketierungs-Metadaten (`store_package.json`):**
   - Vollständige Publisher-DN, Identity-Name und Versionsangabe (`0.2.3.0`) konfiguriert.
   - Lizenzfeld `license: "MIT"` und Sprachen `["de-DE", "en-US"]` hinterlegt.
   - Validierte HTTPS-URLs für Datenschutzrichtlinie und GitHub-Issue-Support hinterlegt.

2. **Windows Desktop AppxManifest (`store_package/CloudLockFixer/AppxManifest.xml`):**
   - Kanonisches AppxManifest mit `TargetDeviceFamily Windows.Desktop` (MinVersion `10.0.17763.0`, MaxVersionTested `10.0.26100.0`).
   - Mehrsprachige Ressourcen (`de-de`, `en-us`) und VisualElements/Tile-Deklarationen eingebunden.
   - Eigenschaften-Logo `<Logo>icons\StoreLogo.png</Logo>` auf standardkonforme 50x50 StoreLogo-Kachel ausgerichtet.

3. **MSIX Tile- und Icon-Assets:**
   - Vollständiges Set an Kachel- und Logo-Assets:
     - `icon_44x44.png` (Square44x44Logo / Square71x71Logo)
     - `icon_50x50.png` (Square50x50Logo)
     - `StoreLogo.png` (50x50 Partner Center StoreLogo)
     - `icon_150x150.png` (Square150x150Logo)
     - `icon_310x150.png` (Wide310x150Logo)
     - `icon_310x310.png` (Square310x310Logo)
   - Synchron gehalten in `store_assets/`, `store_package/CloudLockFixer/icons/` und `releases/windowsstore/`.

4. **Store Screenshots:**
   - Vier hochauflösende 16:9-Präsentationsscreenshots (1920x1080) unter `screenshots/store/`, `README/screenshots/store/` und `releases/windowsstore/screenshots/`:
     - `01_tray-queue-management.png`: Tray-Bedienung & transparente Warteschlangen-Abarbeitung
     - `02_multicloud-provider-support.png`: Multi-Cloud-Provider-Erkennung & Schutz virtueller Mounts
     - `03_preventive-watcher-settings.png`: Präventiver Wächter & konfigurierbare Wiederholungszyklen
     - `04_cross-platform-architecture.png`: Offline-First-, Local-First- & Zero-Egress-Architektur

5. **Bilingualer Store-Listing-Entwurf (`STORE_LISTING.md`):**
   - Vollständige deutsche und englische Beschreibungen mit Feature-Listen.
   - Strikt maximal 7 Suchbegriffe pro Sprache gemäß **Microsoft Store Policy 10.1.3** ohne Fremdmarkenverletzungen.

6. **Automatisiertes Readiness-Audit (`scripts/check_store_readiness.py`):**
   - Automatisierte Validierung aller Manifeste, Metadaten, Icons, Screenshots, Lizenzdokumente und des `releases/windowsstore/` Staging-Pakets.
   - Getestet über Pytest in `tests/test_store_readiness.py`.

## Vor der Einreichung im Partner Center (externe Gates)

- **Partner Center Reservierung:** Identität `Geiger.CloudLockFixer` und Anzeigename `CloudLockFixer` im Microsoft Partner Center bestätigen.
- **MSIX-Erstellung & Signierung:** Produktions-MSIX im Packaging-Workflow erstellen und mit Entwicklerzertifikat signieren.
- **WACK-Zertifizierungstest:** Windows App Certification Kit mit `OVERALL RESULT: PASS` durchlaufen.
- **Partner Center Upload:** Signiertes `.msix`-Paket, Listing-Texte und Screenshots übermitteln.

## Technische Hinweise

- **Lokale Datenhaltung:** CloudLockFixer speichert Konfiguration und Logdateien lokal unter `%LOCALAPPDATA%\CloudLockFixer`.
- **Dateisystem-Schutz:** Virtual Mounts (Google Drive, pCloud) werden vom Wächter-Kill ausgeschlossen, um Mount-Abbrüche zu verhindern.
- **Datenschutz:** 100% Offline-First, keine Telemetrie, kein Tracking.
