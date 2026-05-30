# CloudLockFixer — Portierungsplan (Linux / macOS)

## Übersicht

CloudLockFixer ist aktuell Windows-only. Die Kernlogik (ops.py, models.py, worker.py)
ist bereits plattformneutral. Plattformspezifisch sind:

| Modul | Windows | Linux | macOS |
|-------|---------|-------|-------|
| providers.py | tasklist/taskkill | `pgrep`/`kill` | `pgrep`/`kill`, `launchctl` |
| autostart.py | Registry HKCU\Run | ~/.config/autostart/*.desktop | ~/Library/LaunchAgents/*.plist |
| contextmenu.py | Registry Shell-Extension | Nautilus-Scripts / Nemo-Actions | Finder Quick Actions / Automator |
| paths.py | %LOCALAPPDATA% | ~/.local/share/ (XDG) | ~/Library/Application Support/ |
| tray.py | PySide6 QSystemTrayIcon | PySide6 QSystemTrayIcon | PySide6 QSystemTrayIcon |

## Phase 1: Provider-Abstraktion (Vorarbeit in v1.2.0)

Die Provider-Klassen kapseln bereits die Prozesssteuerung. Für Cross-Platform:

### Prozess-Erkennung

```python
# Windows (aktuell)
subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe}", "/NH"])

# Linux / macOS
subprocess.run(["pgrep", "-f", exe_pattern])
```

### Prozess-Pause/Kill

```python
# Windows (aktuell)
subprocess.run(["taskkill", "/F", "/IM", exe, "/T"])

# Linux
subprocess.run(["kill", "-SIGSTOP", pid])  # Pause (SIGSTOP)
subprocess.run(["kill", "-SIGCONT", pid])  # Resume (SIGCONT)
# Alternativ: kill -9 für Terminate

# macOS
subprocess.run(["kill", "-SIGSTOP", pid])  # Pause
subprocess.run(["kill", "-SIGCONT", pid])  # Resume
# Alternativ via launchctl:
subprocess.run(["launchctl", "stop", service_label])
subprocess.run(["launchctl", "start", service_label])
```

**Vorteil Linux/macOS:** SIGSTOP/SIGCONT pausiert den Prozess OHNE ihn zu beenden.
Das ist sicherer als Windows taskkill (wo es keinen echten Pause-Mechanismus gibt).

### Provider-Roots

| Provider | Linux | macOS |
|----------|-------|-------|
| OneDrive | ~/OneDrive (onedrive-Client/rclone) | ~/Library/CloudStorage/OneDrive-*/ |
| Google Drive | Kein offizieller Client; rclone/Insync | ~/Library/CloudStorage/GoogleDrive-*/ |
| Dropbox | ~/Dropbox | ~/Dropbox oder ~/Library/CloudStorage/Dropbox/ |
| iCloud | Nicht verfügbar | ~/Library/Mobile Documents/com~apple~CloudDocs/ |

## Phase 2: Autostart-Abstraktion

### Linux (XDG Autostart)

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

### macOS (LaunchAgent)

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

## Phase 3: Kontextmenü-Abstraktion

### Linux

- **GNOME/Nautilus:** Script in `~/.local/share/nautilus/scripts/`
- **KDE/Dolphin:** .desktop-Datei in `~/.local/share/kservices5/ServiceMenus/`
- **Nemo:** .nemo_action-Datei in `~/.local/share/nemo/actions/`

### macOS

- **Finder Quick Actions:** Automator-Workflow in `~/Library/Services/`
- Alternativ: Finder-Toolbar-App oder Finder-Extension (komplexer)

## Phase 4: Pfade-Abstraktion

`paths.py` nutzt bereits `os.environ.get("LOCALAPPDATA")` mit Fallback auf
`Path.home() / ".cloudlockfixer"`. Für Linux/macOS:

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

- Kernlogik (ops, models, worker, watcher): Bereits plattformneutral, Tests laufen überall
- Provider-Tests: Komplett gemockt (kein echtes tasklist/pgrep nötig)
- Autostart/Kontextmenü: Integration-Tests nur auf Zielplattform, Unit-Tests gemockt
