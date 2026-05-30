"""Bootstrap-Launcher: legt src/ auf den Pfad und startet CLI (mit Argumenten)
oder die Tray-App (ohne Argumente). Damit funktionieren Registry-Befehle
(Autostart, Kontextmenue) ohne gesetztes PYTHONPATH."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

if len(sys.argv) > 1:
    from cloudlockfixer.cli import main
    raise SystemExit(main(sys.argv[1:]))
else:
    from cloudlockfixer.tray import main
    raise SystemExit(main())
