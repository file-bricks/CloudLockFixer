# CloudLockFixer - Windows Store Build-Anleitung

## Voraussetzungen

1. Python 3.10+ mit PySide6
2. PyInstaller für den Desktop-Build
3. Windows SDK mit `makeappx.exe` und `appcert.exe`
4. Lokaler Schreibpfad außerhalb eines synchronisierten Ordners für große MSIX-Artefakte, z. B. `C:\build\cloudlockfixer-store`

Die Befehle verwenden bewusst Platzhalter statt personenbezogener Arbeitsverzeichnisse.
Setze `$projectRoot` auf den lokalen CloudLockFixer-Checkout und `$softwareRoot` auf den
lokalen `.SOFTWARE`-Pipelineordner, der die Store-Skripte enthält.

## Schritt 0: Store-Material & Screenshots erzeugen

```powershell
$projectRoot = "C:\path\to\CloudLockFixer"
Set-Location $projectRoot
$env:PYTHONIOENCODING="utf-8"
python scripts\generate_store_screenshots.py
```

Erzeugt:
- `releases\windowsstore\screenshots\01_tray-queue-management.png`
- `releases\windowsstore\screenshots\02_multicloud-provider-support.png`
- `releases\windowsstore\screenshots\03_preventive-watcher-settings.png`
- `releases\windowsstore\screenshots\04_cross-platform-architecture.png`
- `screenshots\store\` und `README\screenshots\store\` Kopien

## Schritt 1: Desktop-EXE bauen

```powershell
Set-Location $projectRoot
python -m PyInstaller --noconfirm --onedir --windowed --name CloudLockFixer --icon resources\icon.ico src\cloudlockfixer\__main__.py
```

Erwarteter Hauptpfad:
- `dist\CloudLockFixer\CloudLockFixer.exe`

## Schritt 2: Store-Pretest

```powershell
$softwareRoot = "C:\path\to\.SOFTWARE"
& (Join-Path $softwareRoot "_STORE\msstore_pretest.ps1") `
  -ExePath (Join-Path $projectRoot "dist\CloudLockFixer\CloudLockFixer.exe") `
  -ProjectRoot $projectRoot `
  -StartWait 8
```

## Schritt 3: MSIX lokal außerhalb von OneDrive bauen

```powershell
$outputRoot = "C:\build\cloudlockfixer-store"
& (Join-Path $softwareRoot "_STORE\msstore_build_msix.ps1") `
  -ProjectRoot $projectRoot `
  -ExePath (Join-Path $projectRoot "dist\CloudLockFixer\CloudLockFixer.exe") `
  -OutputMsix (Join-Path $outputRoot "CloudLockFixer.msix") `
  -ExtraFiles @(
    (Join-Path $projectRoot "dist\CloudLockFixer\_internal"),
    (Join-Path $projectRoot "resources")
  )
```

## Schritt 4: WACK als Administrator ausführen

```powershell
$reportRoot = Join-Path $projectRoot "releases\windowsstore\test_reports"
Start-Process powershell -Verb RunAs -ArgumentList @(
  "-ExecutionPolicy Bypass",
  "-File $(Join-Path $softwareRoot '_STORE\msstore_wack.ps1')",
  "-MsixPath $(Join-Path $outputRoot 'CloudLockFixer.msix')",
  "-ReportDir $reportRoot"
)
```

Die Ergebnisse danach in `releases\windowsstore\WACK_PROTOCOL.md` eintragen.
