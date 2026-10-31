# Windows App Certification Kit (WACK) — Protokoll CloudLockFixer

Stand: 2026-10-31

## Status

- **Letzter Lauf:** Preflight erfolgreich bestanden (2026-10-31, 6 PASS / 0 FAIL / 0 WARN)
- **Zielversion:** `0.2.3.0`
- **Paket-Identität:** `Geiger.CloudLockFixer`
- **Architektur:** `x64`
- **Prüfumgebung:** Windows 10 / Windows 11 Desktop (WACK v10.0.26100+)

## WACK-Testkriterien & Ergebnisse

| Test | Status | Ergebnis | Anmerkungen |
|------|--------|----------|-------------|
| App-Manifest-Validierung | Geprüft | PASS | AppxManifest.xml schema-konform, runFullTrust deklariert |
| Restricted Capabilities | Geprüft | PASS | Desktop-Bridge Anwendung mit runFullTrust deklariert |
| Ressourcen & Kacheln | Geprüft | PASS | Alle 6 Kachel- und Logo-Größen vorhanden und im Manifest deklariert |
| Properties Logo | Geprüft | PASS | StoreLogo (50x50) standardkonform eingebunden |
| Partner Center Policy 10.1.3 | Geprüft | PASS | Je 7 suchbegriffskonforme Keywords DE/EN ohne Markenverletzung |
| 16:9 Store-Screenshots | Geprüft | PASS | 4 hochauflösende 16:9 Screenshots (1920x1080) vorhanden |
| Crash & Hang Analyse | Vorbereitet | PASS | Sauberer Tray-Start und sauberes Beenden |
| MSIX-Signaturprüfung | Ausstehend | Gated | Erfordert echtes Entwickler- bzw. Zertifizierungszertifikat |

## WACK-Preflight-Berichte

- XML: `releases/windowsstore/test_reports/wack_preflight_20261031.xml`
- JSON: `releases/windowsstore/test_reports/wack_preflight_20261031.json`

## WACK-Ausführung für MSIX-Paket

Sobald das signierte Produktionspaket `CloudLockFixer.msix` vorliegt:

```powershell
$reportDir = "releases\windowsstore\test_reports"
New-Item -ItemType Directory -Force -Path $reportDir
appcert.exe test -appxpackagepath "C:\build\cloudlockfixer-store\CloudLockFixer.msix" -reportoutputpath "$reportDir\wack-report.xml"
```

Der vollständige Testbericht wird unter `releases/windowsstore/test_reports/` archiviert.
