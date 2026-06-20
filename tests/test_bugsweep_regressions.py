"""Regressionstests: Bugsweep Lauf #10 — CloudLockFixer."""
from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "cloudlockfixer"


# ---------------------------------------------------------------------------
# Bug #10-1: QSystemTrayIcon.Trigger statt QSystemTrayIcon.ActivationReason.Trigger
# ---------------------------------------------------------------------------

def test_tray_uses_activation_reason_enum():
    """_on_activated() muss ActivationReason.Trigger nutzen, nicht deprecated .Trigger (Bug #10-1)."""
    src = (SRC / "tray.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "_on_activated"):
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Compare):
                continue
            for comp in sub.comparators:
                if isinstance(comp, ast.Attribute) and comp.attr == "Trigger":
                    val = comp.value
                    if isinstance(val, ast.Attribute) and val.attr == "ActivationReason":
                        return  # korrekte Form gefunden
                    raise AssertionError(
                        "Bug #10-1: QSystemTrayIcon.Trigger verwendet — "
                        "muss QSystemTrayIcon.ActivationReason.Trigger sein (PySide6 6.4+)"
                    )
    # kein Compare mit .Trigger gefunden — ebenfalls OK (kein Vergleich)


# ---------------------------------------------------------------------------
# Bug #10-2: _ingest_txt() kein try/except OSError bei write_text/replace
# ---------------------------------------------------------------------------

def test_ingest_txt_survives_oserror(tmp_path):
    """_ingest_txt() darf bei OSError beim Schreiben nicht abstürzen (Bug #10-2)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from unittest.mock import patch
    from cloudlockfixer.models import Queue

    q = Queue(tmp_path)
    txt = tmp_path / "queue.txt"
    txt.write_text("delete /some/path\n", encoding="utf-8")

    with patch("pathlib.Path.write_text", side_effect=OSError("locked")):
        try:
            q.load()
        except OSError:
            raise AssertionError("_ingest_txt() muss OSError intern abfangen (Bug #10-2)")


# ---------------------------------------------------------------------------
# Bug #10-3: settings.save() kein try/except OSError
# ---------------------------------------------------------------------------

def test_settings_save_survives_oserror(tmp_path):
    """settings.save() darf bei OSError nicht abstürzen (Bug #10-3)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from unittest.mock import patch
    import cloudlockfixer.settings as s

    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        try:
            s.save({"interval_min": 60})
        except OSError:
            raise AssertionError("settings.save() muss OSError intern abfangen (Bug #10-3)")


# ---------------------------------------------------------------------------
# Bug #10-4: ops.py User-facing Strings mit ASCII-Digraphen
# ---------------------------------------------------------------------------

def test_ops_no_digraphs_in_return_strings():
    """ops.py return-Strings dürfen keine ASCII-Digraphe enthalten (Bug #10-4)."""
    import re
    src = (SRC / "ops.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    digraph_re = re.compile(
        r"\b(?:geloescht|uebersprungen|loeschen|unvollstaendig|spaeter|"
        r"fuer|rueckgabe|fuehrt|verzoegert|naechste)\b",
        re.IGNORECASE,
    )
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            m = digraph_re.search(node.value)
            if m:
                violations.append(f"Z.{node.lineno}: '{m.group()}'")
    assert not violations, (
        "ASCII-Digraphe in ops.py Strings (Bug #10-4) — echte Umlaute verwenden:\n"
        + "\n".join(violations)
    )
