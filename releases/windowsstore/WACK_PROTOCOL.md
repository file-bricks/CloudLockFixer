# Windows App Certification Kit (WACK) — Protokoll CloudLockFixer

Stand: 2026-09-23

## Status

- **Letzter Lauf:** Ausstehend (Staging-Phase vor Zertifizierung)
- **Zielversion:** `0.2.3.0`
- **Paket-Identität:** `Geiger.CloudLockFixer`
- **Architektur:** `x64`
- **Prüfumgebung:** Windows 10 / Windows 11 Desktop (WACK v10.0.26100+)

## WACK-Testkriterien & Erwartungshaltung

| Test | Status | Erwartetes Ergebnis | Anmerkungen |
|------|--------|---------------------|-------------|
| App-Manifest-Validierung | Vorbereitet | PASS | AppxManifest.xml schema-konform, runFullTrust deklariert |
| Binär-Sicherheit (NX, SafeSEH, ASLR) | Vorbereitet | PASS | PyInstaller-Kompilate mit standardmäßigem Speicherschutz |
| Unterstützte APIs | Vorbereitet | PASS | Desktop-Bridge Anwendung mit runFullTrust deklariert |
| Ressourcen & Kacheln | Vorbereitet | PASS | Alle Tile-Größen vorhanden und im Manifest deklariert |
| Crash & Hang Analyse | Vorbereitet | PASS | Sauberer Tray-Start und sauberes Beenden |
| MSIX-Signaturprüfung | Ausstehend | Gated | Erfordert echtes Entwickler- bzw. Zertifizierungszertifikat |

## WACK-Ausführung

Sobald das signierte Produktionspaket `CloudLockFixer.msix` vorliegt:

```powershell
$reportDir = "releases\windowsstore\test_reports"
New-Item -ItemType Directory -Force -Path $reportDir
appcert.exe test -appxpackagepath "C:\build\cloudlockfixer-store\CloudLockFixer.msix" -reportoutputpath "$reportDir\wack-report.xml"
```

Der vollständige Testbericht wird unter `releases/windowsstore/test_reports/` archiviert.
