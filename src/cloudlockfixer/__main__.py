"""`python -m cloudlockfixer` startet ohne Argumente die Tray-App, mit
Argumenten die CLI (analog zu clf_launcher.pyw und clf_app.py)."""
import sys

if len(sys.argv) > 1:
    from .cli import main as cli_main

    raise SystemExit(cli_main(sys.argv[1:]))

from .tray import main

raise SystemExit(main())
