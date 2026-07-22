# CloudLockFixer — Portierungsplan (Linux / macOS)

## Übersicht

Der paketierte Release von CloudLockFixer ist aktuell Windows-only. Die Kernlogik
(ops.py, models.py, worker.py) ist bereits plattformneutral; Linux-XDG-Autostart
ist seit 2026-07-18 auf Source-Ebene umgesetzt. Plattformspezifisch sind:

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

## Phase 3: Kontextmenü-Abstraktion

### Linux

- **GNOME/Nautilus:** Script in `~/.local/share/nautilus/scripts/`
- **KDE/Dolphin:** .desktop-Datei in `~/.local/share/kservices5/ServiceMenus/`
- **Nemo:** .nemo_action-Datei in `~/.local/share/nemo/actions/`

### macOS

- **Finder Quick Actions:** Automator-Workflow in `~/Library/Services/`
- Alternativ: Finder-Toolbar-App oder Finder-Extension (komplexer)

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

Revalidiert 2026-07-22: Die vollständige lokale Suite umfasst 164 Tests; zusätzlich
bestand bereits ein echter Ubuntu-/WSL-Roundtrip für den Linux-XDG-Autostart.
Damit sind Linux-/macOS-Source-Smokes, Linux-XDG-Autostart und macOS-LaunchAgent
auf Source-Ebene abgeschlossen. Offen bleiben native Linux-/macOS-Pakete, ein
echter Mac-Login-/`launchctl`-/GUI-/Cloud-Client-Smoke und plattformspezifische
Kontextmenüs.
