# -*- coding: utf-8 -*-
"""PyInstaller-Entry fuer CloudLockFixer.
Ohne Argumente -> Tray-App; mit Argumenten -> CLI (z.B. 'CloudLockFixer.exe list')."""
import os
import sys

if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


def main() -> int:
    argv = sys.argv[1:]
    if argv:
        from cloudlockfixer.cli import main as cli_main
        return cli_main(argv)
    from cloudlockfixer.tray import main as tray_main
    return tray_main()


if __name__ == "__main__":
    sys.exit(main())
