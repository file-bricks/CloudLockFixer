"""CLI — fuer LLM/Skripte und manuelles Einreihen.

Beispiele:
  clf add --rename "C:\\...\\AltOrdner" "NeuName"
  clf add --move "C:\\local\\x" "C:\\onedrive\\x"
  clf add --delete "C:\\onedrive\\alt"
  clf add --chain 'move "C:\\local\\x" "C:\\onedrive\\x" && delete "C:\\onedrive\\alt"'
  clf list
  clf run-now [--pause]
"""
from __future__ import annotations

import argparse
import logging
import sys

from .models import Queue, Step, Task, parse_txt_line
from .paths import data_dir, log_file
from .worker import run_once


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file(), encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clf", description="CloudLockFixer CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Task einreihen")
    g = p_add.add_mutually_exclusive_group(required=True)
    g.add_argument("--rename", nargs=2, metavar=("PFAD", "NEUNAME"))
    g.add_argument("--move", nargs=2, metavar=("QUELLE", "ZIEL"))
    g.add_argument("--delete", nargs=1, metavar="PFAD")
    g.add_argument("--chain", metavar="AUSDRUCK",
                   help="z.B. 'move \"a\" \"b\" && delete \"c\"'")

    sub.add_parser("list", help="Queue anzeigen")
    p_run = sub.add_parser("run-now", help="Queue jetzt abarbeiten")
    p_run.add_argument("--pause", action="store_true",
                       help="Sync-Client fuer den Lauf pausieren (M2)")

    p_ctx = sub.add_parser("context", help="Explorer-Kontextmenue verwalten")
    gc = p_ctx.add_mutually_exclusive_group(required=True)
    gc.add_argument("--install", action="store_true")
    gc.add_argument("--uninstall", action="store_true")
    gc.add_argument("--status", action="store_true")

    p_gui = sub.add_parser("gui-add", help="Dialog zum Einreihen (vom Kontextmenue)")
    p_gui.add_argument("--op", required=True, choices=["rename", "move", "delete"])
    p_gui.add_argument("--src", required=True)

    args = parser.parse_args(argv)
    _setup_logging()
    queue = Queue(data_dir())

    if args.cmd == "add":
        if args.rename:
            task = Task(chain=[Step(op="rename", src=args.rename[0], arg=args.rename[1])])
        elif args.move:
            task = Task(chain=[Step(op="move", src=args.move[0], arg=args.move[1])])
        elif args.delete:
            task = Task(chain=[Step(op="delete", src=args.delete[0])])
        else:
            task = parse_txt_line(args.chain)  # type: ignore[assignment]
            if task is None:
                print("Leere/ungueltige Kette.", file=sys.stderr)
                return 2
        queue.add(task)
        print(f"Eingereiht: {task.id}  {task.describe()}")
        return 0

    if args.cmd == "list":
        if not queue.tasks:
            print("Queue leer.")
            return 0
        for t in queue.tasks:
            print(f"[{t.status:7}] {t.id}  (Versuche {t.retry_count})  {t.describe()}"
                  + (f"  ! {t.last_error}" if t.last_error else ""))
        return 0

    if args.cmd == "run-now":
        summary = run_once(queue, force_pause=args.pause)
        print(f"Lauf fertig: {summary['done']} erledigt, "
              f"{summary['failed_again']} weiterhin offen "
              f"(Start: {summary['pending_start']} offen)."
              + (f" Pausiert: {', '.join(summary['paused_providers'])}"
                 if summary['paused_providers'] else ""))
        return 0

    if args.cmd == "context":
        from . import contextmenu
        if args.install:
            ok = contextmenu.install()
            print("Kontextmenue installiert." if ok else "Installation fehlgeschlagen.")
            return 0 if ok else 1
        if args.uninstall:
            ok = contextmenu.uninstall()
            print("Kontextmenue entfernt." if ok else "Entfernen fehlgeschlagen.")
            return 0 if ok else 1
        print("installiert" if contextmenu.is_installed() else "nicht installiert")
        return 0

    if args.cmd == "gui-add":
        return _gui_add(args.op, args.src, queue)

    return 1


def _gui_add(op: str, src: str, queue: Queue) -> int:
    """Mini-GUI-Dialog (vom Explorer-Kontextmenue aufgerufen)."""
    import os

    from PySide6.QtWidgets import (
        QApplication, QFileDialog, QInputDialog, QMessageBox,
    )

    app = QApplication.instance() or QApplication(sys.argv)
    _ = app
    name = os.path.basename(src.rstrip("/\\"))
    if op == "rename":
        new, ok = QInputDialog.getText(
            None, "Verzoegert umbenennen", f"Neuer Name fuer:\n{src}", text=name)
        if not ok or not new.strip():
            return 0
        task = Task(chain=[Step(op="rename", src=src, arg=new.strip())])
    elif op == "move":
        dst_parent = QFileDialog.getExistingDirectory(None, "Zielordner waehlen")
        if not dst_parent:
            return 0
        task = Task(chain=[Step(op="move", src=src,
                                arg=os.path.join(dst_parent, name))])
    else:
        if QMessageBox.question(None, "Verzoegert loeschen",
                                f"'{src}'\nverzoegert loeschen?") != QMessageBox.StandardButton.Yes:
            return 0
        task = Task(chain=[Step(op="delete", src=src)])
    queue.add(task)
    QMessageBox.information(None, "CloudLockFixer",
                           f"Eingereiht:\n{task.describe()}\n\n"
                           "Wird beim naechsten Lauf erledigt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
