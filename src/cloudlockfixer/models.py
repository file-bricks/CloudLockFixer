"""Datenmodell + Queue-Store (queue.json + benutzerfreundliche queue.txt)."""
from __future__ import annotations

import json
import shlex
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

StepType = Literal["rename", "move", "delete"]
Status = Literal["pending", "running", "done", "failed"]

_VALID_OPS = ("rename", "move", "delete")


@dataclass
class Step:
    """Ein Schritt einer Kette.

    rename: src + arg (neuer Name, ohne Pfad)
    move:   src + arg (Zielpfad)
    delete: src
    """
    op: StepType
    src: str
    arg: str = ""
    copied: bool = False  # bei move/rename: Copy erfolgt, nur noch Quelle-Loeschen offen

    def describe(self) -> str:
        if self.op == "rename":
            return f"rename '{self.src}' -> '{self.arg}'"
        if self.op == "move":
            return f"move '{self.src}' -> '{self.arg}'"
        return f"delete '{self.src}'"


@dataclass
class Task:
    chain: list[Step]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: Status = "pending"
    retry_count: int = 0
    created_at: str = ""
    last_try: str = ""
    last_error: str = ""
    step_index: int = 0  # nächster auszuführender Schritt (für Wiederaufnahme)

    def describe(self) -> str:
        return " && ".join(s.describe() for s in self.chain)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["chain"] = [asdict(s) for s in self.chain]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        chain = [Step(**s) for s in d.get("chain", [])]
        known = {f for f in cls.__dataclass_fields__ if f != "chain"}
        return cls(chain=chain, **{k: v for k, v in d.items() if k in known})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_txt_line(line: str) -> Task | None:
    """Parst eine queue.txt-Zeile in einen Task.

    Syntax (Pfade mit Leerzeichen in \"...\"):
        rename <pfad> <neuerName>
        move <quelle> <ziel>
        delete <pfad>
        Verkettung mit '&&':  move <a> <b> && delete <c>
    Leerzeilen und '#'-Kommentare werden ignoriert.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    steps: list[Step] = []
    for part in line.split("&&"):
        tokens = shlex.split(part.strip())
        if not tokens:
            continue
        op = tokens[0].lower()
        if op not in _VALID_OPS:
            raise ValueError(f"Unbekannte Operation '{op}' in: {part!r}")
        if op == "delete":
            if len(tokens) != 2:
                raise ValueError(f"'delete' braucht genau einen Pfad: {part!r}")
            steps.append(Step(op="delete", src=tokens[1]))
        else:
            if len(tokens) != 3:
                raise ValueError(f"'{op}' braucht Quelle und Ziel/Name: {part!r}")
            steps.append(Step(op=op, src=tokens[1], arg=tokens[2]))  # type: ignore[arg-type]
    if not steps:
        return None
    return Task(chain=steps, created_at=_now())


class Queue:
    """Persistente Queue: queue.json (Programm) + queue.txt (Mensch/LLM)."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.data_dir / "queue.json"
        self.txt_path = self.data_dir / "queue.txt"
        self.tasks: list[Task] = []
        self._lock = threading.Lock()
        self.load()

    def load(self) -> None:
        with self._lock:
            self.tasks = []
            if self.json_path.exists():
                try:
                    raw = json.loads(self.json_path.read_text(encoding="utf-8"))
                    if not isinstance(raw, dict):
                        raise TypeError(f"unexpected JSON root type: {type(raw)}")
                    self.tasks = [Task.from_dict(t) for t in raw.get("tasks", [])]
                except (json.JSONDecodeError, OSError, TypeError, AttributeError):
                    self.tasks = []
            self._ingest_txt()

    def _ingest_txt(self) -> None:
        """Liest neue Zeilen aus queue.txt, hängt sie als Tasks an und
        kommentiert sie in der txt-Datei aus (so werden sie nicht doppelt
        aufgenommen, bleiben aber als Historie sichtbar)."""
        if not self.txt_path.exists():
            self.txt_path.write_text(_txt_header(), encoding="utf-8")
            return
        lines = self.txt_path.read_text(encoding="utf-8").splitlines()
        changed = False
        out: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                out.append(line)
                continue
            try:
                task = parse_txt_line(line)
            except ValueError as e:
                from .i18n import t
                out.append(f"# {t('parse_error')}: {e}")
                out.append(f"# {line}")
                changed = True
                continue
            if task is not None:
                self.tasks.append(task)
                out.append(f"#> aufgenommen {task.id}: {line.strip()}")
                changed = True
            else:
                out.append(line)
        if changed:
            tmp = self.txt_path.with_suffix(".txt.tmp")
            tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
            tmp.replace(self.txt_path)
            self._save_unlocked()

    def add(self, task: Task) -> Task:
        with self._lock:
            if not task.created_at:
                task.created_at = _now()
            self.tasks.append(task)
            self._save_unlocked()
        return task

    @property
    def pending(self) -> list[Task]:
        return [t for t in self.tasks if t.status in ("pending", "running")]

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        payload = {"version": 1, "saved_at": _now(),
                   "tasks": [t.to_dict() for t in self.tasks]}
        tmp = self.json_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.json_path)


def _txt_header() -> str:
    from .i18n import t
    return t("queue_txt_header")
