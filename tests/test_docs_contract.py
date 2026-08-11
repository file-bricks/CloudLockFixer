from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import cloudlockfixer

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _collect_pytest_count() -> int:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout)
    assert match, result.stdout
    return int(match.group(1))


def test_llms_release_version_matches_package_version() -> None:
    text = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
    assert f"Release version: {cloudlockfixer.__version__}" in text

    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject)
    assert project_version and project_version.group(1) == cloudlockfixer.__version__
    assert 'state = "unreleased"' in pyproject
    assert 'baseline_tag = "v0.2.2"' in pyproject

    release_gate = (PROJECT_ROOT / "RELEASE_GATE.md").read_text(encoding="utf-8")
    assert "Kanonische Source-Version:** `0.2.2`" in release_gate
    assert "Historischer Initial-Tag:** `v1.0.0`" in release_gate


def test_docs_reference_current_collected_test_count() -> None:
    count = _collect_pytest_count()
    expectations = {
        PROJECT_ROOT / "README.md": rf"`pytest`, {count} passing",
        PROJECT_ROOT / "README.de.md": rf"`pytest`, \*\*{count} grün\*\*",
        PROJECT_ROOT / "llms.txt": rf"with {count}\s+passing tests",
        PROJECT_ROOT / "CHANGELOG.md": rf"reflects the current unreleased source state: {count} passing",
    }
    for path, pattern in expectations.items():
        text = path.read_text(encoding="utf-8")
        assert re.search(pattern, text), path.name
