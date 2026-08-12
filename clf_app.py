# -*- coding: utf-8 -*-
"""PyInstaller-Entry fuer CloudLockFixer.
Ohne Argumente -> Tray-App; mit Argumenten -> CLI (z.B. 'CloudLockFixer.exe list')."""
import os
import sys
import logging
from pathlib import Path

def _configure_early_logging() -> None:
    """Capture import/start failures before tray or CLI modules are imported."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "CloudLockFixer"
    base.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(base / "startup.log", encoding="utf-8")])

_configure_early_logging()

if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


def main() -> int:
    try:
        argv = sys.argv[1:]
        if argv:
            from cloudlockfixer.cli import main as cli_main
            return cli_main(argv)
        from cloudlockfixer.tray import main as tray_main
        return tray_main()
    except Exception:
        logging.exception("CloudLockFixer startup failed")
        raise


if __name__ == "__main__":
    sys.exit(main())
