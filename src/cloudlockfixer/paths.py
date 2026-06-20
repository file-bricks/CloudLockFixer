"""Zentrale Pfade (Datenverzeichnis, Log, Launcher für Registry-Befehle)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    # cloudlockfixer/paths.py -> [0]=cloudlockfixer [1]=src [2]=Projekt
    return Path(__file__).resolve().parents[2]


def launcher() -> Path:
    """Bootstrap-Skript, das src auf den Pfad legt und CLI/Tray startet."""
    return project_root() / "clf_launcher.pyw"


def pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        return exe[: -len("python.exe")] + "pythonw.exe"
    return exe


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "CloudLockFixer" if base else Path.home() / ".cloudlockfixer"
    root.mkdir(parents=True, exist_ok=True)
    return root


def log_file() -> Path:
    return data_dir() / "clf.log"
