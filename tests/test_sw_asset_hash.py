"""Fuehrt den Service-Worker-Waechter (ASSET_HASH) aus; ohne Node.js wird er uebersprungen."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")
def test_sw_asset_hash_waechter():
    res = subprocess.run(
        ["node", "--test", "web_companion/tests/sw_asset_hash.test.mjs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res.returncode == 0, f"{res.stdout}\n{res.stderr}"
