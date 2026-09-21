# CloudLockFixer — Portierungsplan (Linux / macOS)

## Übersicht

Der paketierte Release von CloudLockFixer ist aktuell Windows-only. Die Kernlogik
(ops.py, models.py, worker.py) ist bereits plattformneutral; Linux-XDG-Autostart
ist seit 2026-07-18 auf Source-Ebene umgesetzt. Plattformspezifisch sind:

| Modul | Windows | Linux | macOS |
|-------|---------|-------|-------|
| providers.py | tasklist/taskkill | `pgrep`/`pkill` (umgesetzt) | `pgrep`/`pkill`, `open` (umgesetzt) |
| autostart.py | Registry HKCU\Run | ~/.config/autostart/*.desktop | ~/Library/LaunchAgents/*.plist |
| contextmenu.py | Registry Shell-Extension | Nautilus-Scripts / Nemo-Actions | Finder Quick Actions / Automator |
| paths.py | %LOCALAPPDATA% | ~/.local/share/ (XDG) | ~/Library/Application Support/ |
| tray.py | PySide6 QSystemTrayIcon | PySide6 QSystemTrayIcon | PySide6 QSystemTrayIcon |

## Phase 1: Provider-Abstraktion (umgesetzt 2026-09-08)

Die Provider-Klassen kapseln die plattformübergreifende Prozess- und Pfadsteuerung.
Seit 2026-09-08 ist Phase 1 auf Source-Ebene vollständig umgesetzt:

### Prozess-Erkennung (`_check_process`)
- **Windows:** `tasklist /FI IMAGENAME eq <exe> /NH`
- **Linux / macOS:** `pgrep -f <pattern>` mit Fallback auf `/proc/<pid>/cmdline` auf Linux.
- **Pattern-Mapping:** `_PROCESS_ALIASES_POSIX` mappt Windows-Executable-Namen (z. B. `GoogleDriveFS.exe`, `cloud-drive-ui.exe`, `OneDrive.exe`) auf die jeweiligen POSIX-Prozessmuster (`Google Drive`, `synology-drive`, `onedrive`, `bird`).

### Prozess-Pause / Beendigung (`_kill_process`)
- **Windows:** `taskkill /F /IM <exe> /T`
- **Linux / macOS:** `pkill -f <pattern>` mit Grace-Period und Verifikation.

### Provider-Roots
Vollständige Erkennung nativer Cloud-Sync-Pfade unter Linux und macOS:
| Provider | Linux | macOS |
|----------|-------|-------|
| OneDrive | ~/OneDrive (onedrive Client) | ~/Library/CloudStorage/OneDrive-*/ |
| Google Drive | Insync / rclone | ~/Library/CloudStorage/GoogleDrive-*/ |
| Dropbox | ~/.dropbox/info.json, ~/Dropbox | ~/Library/Application Support/Dropbox/info.json, ~/Library/CloudStorage/Dropbox/ |
| Box | ~/Box | ~/Library/CloudStorage/Box-*/ |
| Nextcloud | ~/.config/Nextcloud/nextcloud.cfg | ~/Library/Preferences/Nextcloud/nextcloud.cfg |
| pCloud | ~/pCloudDrive | ~/pCloudDrive |
| Synology Drive | ~/.SynologyDrive | ~/Library/Application Support/SynologyDrive |
| iCloud | N/A | ~/Library/Mobile Documents/com~apple~CloudDocs/ |

### Provider-Resume
- **macOS:** `open -a <App-Name>` für alle Desktop-Clients.
- **Linux:** Executable-Erkennung per `shutil.which()` mit `--background` bzw. `start` Flags.

## Phase 2: Autostart-Abstraktion

### Linux (XDG Autostart) — umgesetzt 2026-07-18

`src/cloudlockfixer/autostart.py` nutzt `$XDG_CONFIG_HOME/autostart` mit
`~/.config/autostart` als Fallback. Der Eintrag wird atomar geschrieben, gegen
den aktuellen Startbefehl validiert und idempotent entfernt.

Datei: `~/.config/autostart/cloudlockfixer.desktop`
```ini
[Desktop Entry]
Type=Application
Name=CloudLockFixer
Exec=pythonw /path/to/clf_launcher.pyw
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### macOS (LaunchAgent) — umgesetzt 2026-07-22

`src/cloudlockfixer/autostart.py` erzeugt die plist atomar mit `plistlib`,
validiert Label, aktuelle `ProgramArguments`, `RunAtLoad` und `KeepAlive` und
entfernt den Eintrag idempotent. Die Konfiguration gilt beim nächsten Login;
ein laufender Agent wird bewusst nicht automatisch per `launchctl` verändert.

Datei: `~/Library/LaunchAgents/com.cloudlockfixer.agent.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.cloudlockfixer.agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/path/to/clf_launcher.pyw</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
```

## Phase 3: Kontextmenü-Abstraktion (erledigt auf Source-Ebene 2026-09-21)

Stand 2026-09-21: `contextmenu.py` abstrahiert plattformübergreifend:
- **Windows:** HKCU-Registry (`Directory\shell\CloudLockFixer` und `*\shell\CloudLockFixer`)
- **Linux:** Nautilus-Skripte in `$XDG_DATA_HOME/nautilus/scripts/CloudLockFixer/` (`01_delayed_rename.sh`, `02_delayed_move.sh`, `03_delayed_delete.sh`) mit `0o755` und KDE/Dolphin ServiceMenu in `$XDG_DATA_HOME/kio/servicemenus/cloudlockfixer.desktop`.
- **macOS:** Finder Quick Actions / Services-Workflows in `~/Library/Services/` (`CloudLockFixer - Delayed Rename.workflow`, `Move.workflow`, `Delete.workflow`) mit `Info.plist` und `document.wflow`.
Abgedeckt durch `tests/test_contextmenu_cross_platform.py` und `tests/source_platform_smoke.py`.

## Phase 4: Pfade-Abstraktion

Stand 2026-07-14: `paths.data_dir()` ist als Source-Level-Portierung umgesetzt
und durch `tests/test_paths_cross_platform.py` abgedeckt. Die Laufzeitpfade sind:

```python
def data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / "CloudLockFixer" if base else Path.home() / ".cloudlockfixer"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "CloudLockFixer"
    # Linux (XDG)
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "cloudlockfixer"
```

Nicht abgedeckt sind weiterhin echte Zielplattform-Installer, ein realer
Mac-Login-/`launchctl`-/GUI-/Cloud-Client-Smoke und Linux-/macOS-
Kontextmenümechanismen.

## Phase 5: Build-Abstraktion

| Plattform | Build-Tool | Ausgabe |
|-----------|------------|---------|
| Windows | PyInstaller --onedir | CloudLockFixer.exe |
| Linux | PyInstaller oder AppImage | cloudlockfixer (AppImage) |
| macOS | PyInstaller --onedir + py2app | CloudLockFixer.app |

CI/CD: GitHub Actions Matrix-Build (windows-latest, ubuntu-latest, macos-latest).

## Priorisierung

1. **Hoch:** Provider-Abstraktion (Grundlage für alles andere)
2. **Mittel:** Pfade + Autostart (funktionale Basis)
3. **Niedrig:** Kontextmenü (Nice-to-have, plattformspezifisch komplex)
4. **Später:** Build + CI/CD (erst wenn Code stabil auf allen Plattformen)

## Testbarkeit

- Kernlogik (ops, models, worker, watcher): Bereits plattformneutral, Tests laufen überall ✓
- Provider-Tests: Komplett gemockt (kein echtes tasklist/pgrep nötig)
- Autostart/Kontextmenü: Integration-Tests nur auf Zielplattform, Unit-Tests gemockt

### Source-Platform Smoke-Tests (CI aktiv)

`tests/source_platform_smoke.py` + `.github/workflows/source-platform-smoke.yml` prüfen auf
`ubuntu-latest` und `macos-latest` headless: Import, Version, ops, Queue, paths und
worker; auf Linux zusätzlich den XDG-Autostart-Roundtrip und auf macOS den
LaunchAgent-plist-Roundtrip. Kein Cloud-Client, kein GUI, kein pip-Extra (nur
pytest). Stand: 2026-07-22.

Revalidiert 2026-09-21: Die vollständige lokale Suite umfasst 277 Tests (100% grün).
Damit sind Linux-/macOS-Source-Smokes, Linux-XDG-Autostart, macOS-LaunchAgent und
plattformübergreifende Kontextmenüs (Linux Nautilus & KDE Dolphin, macOS Services)
auf Source-Ebene vollständig umgesetzt und abgesichert. Offen bleiben native
Linux-/macOS-Pakete/Installer (Task 171) und ein nativer Mac-Login-/`launchctl`-Smoke.
