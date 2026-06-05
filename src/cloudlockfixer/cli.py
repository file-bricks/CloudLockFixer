"""CLI — für LLM/Skripte und manuelles Einreihen.

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

from . import i18n, settings
from .i18n import t
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
    cfg = settings.load()
    i18n.set_language(settings.resolve_language(cfg))

    parser = argparse.ArgumentParser(prog="clf", description=t("cli_desc"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help=t("cli_add_help"))
    g = p_add.add_mutually_exclusive_group(required=True)
    g.add_argument("--rename", nargs=2, metavar=("PFAD", "NEUNAME"))
    g.add_argument("--move", nargs=2, metavar=("QUELLE", "ZIEL"))
    g.add_argument("--delete", nargs=1, metavar="PFAD")
    g.add_argument("--chain", metavar="AUSDRUCK",
                   help="z.B. 'move \"a\" \"b\" && delete \"c\"'")

    sub.add_parser("list", help=t("cli_list_help"))
    p_run = sub.add_parser("run-now", help=t("cli_run_help"))
    p_run.add_argument("--pause", action="store_true",
                       help=t("cli_pause_help"))

    p_ctx = sub.add_parser("context", help=t("cli_context_help"))
    gc = p_ctx.add_mutually_exclusive_group(required=True)
    gc.add_argument("--install", action="store_true")
    gc.add_argument("--uninstall", action="store_true")
    gc.add_argument("--status", action="store_true")

    p_gui = sub.add_parser("gui-add", help=t("cli_gui_add_help"))
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
            try:
                task = parse_txt_line(args.chain)  # type: ignore[assignment]
            except ValueError as e:
                print(t("invalid_chain") + f": {e}", file=sys.stderr)
                return 2
            if task is None:
                print(t("invalid_chain"), file=sys.stderr)
                return 2
        queue.add(task)
        print(t("queued_msg", id=task.id, desc=task.describe()))
        return 0

    if args.cmd == "list":
        if not queue.tasks:
            print(t("queue_empty"))
            return 0
        for tk in queue.tasks:
            print(f"[{tk.status:7}] {tk.id}  (Versuche {tk.retry_count})  {tk.describe()}"
                  + (f"  ! {tk.last_error}" if tk.last_error else ""))
        return 0

    if args.cmd == "run-now":
        summary = run_once(queue, force_pause=args.pause)
        paused = ""
        if summary["paused_providers"]:
            paused = t("paused_providers",
                       names=", ".join(summary["paused_providers"]))
        print(t("run_summary", done=summary["done"],
                failed=summary["failed_again"],
                start=summary["pending_start"], paused=paused))
        return 0

    if args.cmd == "context":
        from . import contextmenu
        if args.install:
            ok = contextmenu.install()
            print(t("context_installed") if ok else t("context_install_failed"))
            return 0 if ok else 1
        if args.uninstall:
            ok = contextmenu.uninstall()
            print(t("context_removed") if ok else t("context_remove_failed"))
            return 0 if ok else 1
        print(t("context_status_installed") if contextmenu.is_installed()
              else t("context_status_not_installed"))
        return 0

    if args.cmd == "gui-add":
        return _gui_add(args.op, args.src, queue)

    return 1


def _gui_add(op: str, src: str, queue: Queue) -> int:
    import os

    from PySide6.QtWidgets import (
        QApplication, QFileDialog, QInputDialog, QMessageBox,
    )

    app = QApplication.instance() or QApplication(sys.argv)
    _ = app
    name = os.path.basename(src.rstrip("/\\"))
    if op == "rename":
        new, ok = QInputDialog.getText(
            None, t("gui_rename_title"),
            t("gui_rename_prompt", src=src), text=name)
        if not ok or not new.strip():
            return 0
        task = Task(chain=[Step(op="rename", src=src, arg=new.strip())])
    elif op == "move":
        dst_parent = QFileDialog.getExistingDirectory(None, t("gui_move_title"))
        if not dst_parent:
            return 0
        task = Task(chain=[Step(op="move", src=src,
                                arg=os.path.join(dst_parent, name))])
    else:
        if QMessageBox.question(
                None, t("gui_delete_title"),
                t("gui_delete_confirm", src=src)
        ) != QMessageBox.StandardButton.Yes:
            return 0
        task = Task(chain=[Step(op="delete", src=src)])
    queue.add(task)
    QMessageBox.information(None, t("gui_queued_title"),
                           t("gui_queued_msg", desc=task.describe()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
