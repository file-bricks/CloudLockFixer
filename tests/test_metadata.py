from __future__ import annotations

import ast
from pathlib import Path


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_pep621_metadata() -> None:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    project = data.get("project", {})
    assert project.get("name") == "cloudlockfixer"
    assert project.get("version") == "0.2.3"
    assert project.get("license") == {"text": "MIT"}
    assert project.get("requires-python") == ">=3.10"

    authors = project.get("authors", [])
    assert any(a.get("name") == "file-bricks" for a in authors)

    classifiers = project.get("classifiers", [])
    required_classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ]
    for classifier in required_classifiers:
        assert classifier in classifiers, f"Missing classifier: {classifier}"

    keywords = project.get("keywords", [])
    assert isinstance(keywords, list)
    assert len(keywords) >= 5
    assert "cldflt" in keywords
    assert "local-first" in keywords


def test_project_urls_integrity() -> None:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    urls = data.get("project", {}).get("urls", {})

    expected_keys = [
        "Homepage",
        "Documentation",
        "Repository",
        "Bug Tracker",
        "Changelog",
        "Security Policy",
        "Parent Org",
        "Umbrella Ecosystem",
    ]
    for key in expected_keys:
        assert key in urls, f"Missing project.urls entry: {key}"
        assert urls[key].startswith("https://github.com/"), f"Invalid URL for {key}: {urls[key]}"


def test_security_policy_and_offline_invariants() -> None:
    sec_path = PROJECT_ROOT / "SECURITY.md"
    assert sec_path.is_file(), "SECURITY.md must exist"
    sec_text = sec_path.read_text(encoding="utf-8")

    assert "## Deutsch" in sec_text
    assert "## English" in sec_text
    assert "security@ellmos.ai" in sec_text
    assert "lukas@open-bricks.org" in sec_text
    assert "support@lukasgeiger.com" in sec_text
    assert "info@file-bricks.org" in sec_text
    assert "https://github.com/file-bricks/CloudLockFixer/security/advisories/new" in sec_text
    assert "Zero-Egress" in sec_text
    assert "Local-First" in sec_text


def test_offline_zero_egress_no_network_imports() -> None:
    forbidden_modules = {
        "urllib.request",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "http.client",
        "ftplib",
        "smtplib",
    }
    src_dir = PROJECT_ROOT / "src" / "cloudlockfixer"
    assert src_dir.is_dir(), "src/cloudlockfixer must exist"

    for py_file in src_dir.glob("**/*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, (
                        f"Forbidden network module '{alias.name}' in {py_file.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module not in forbidden_modules, (
                        f"Forbidden network module '{node.module}' in {py_file.name}"
                    )


def test_ci_workflow_integrity() -> None:
    workflows_dir = PROJECT_ROOT / ".github" / "workflows"
    assert workflows_dir.is_dir(), ".github/workflows must exist"

    tests_yml = (workflows_dir / "tests.yml").read_text(encoding="utf-8")
    assert "concurrency:" in tests_yml
    assert "cancel-in-progress: true" in tests_yml
    assert 'python-version: ["3.10", "3.11", "3.12", "3.13"]' in tests_yml
    assert "ruff check ." in tests_yml
    assert "actions/checkout@v4" in tests_yml
    assert "actions/setup-python@v5" in tests_yml

    smoke_yml = (workflows_dir / "source-platform-smoke.yml").read_text(encoding="utf-8")
    assert "concurrency:" in smoke_yml
    assert "cancel-in-progress: true" in smoke_yml
    assert "actions/checkout@v4" in smoke_yml
    assert "actions/setup-python@v5" in smoke_yml


def test_bilingual_readme_parity() -> None:
    readme_en = PROJECT_ROOT / "README.md"
    readme_de = PROJECT_ROOT / "README.de.md"

    assert readme_en.is_file(), "README.md must exist"
    assert readme_de.is_file(), "README.de.md must exist"

    text_en = readme_en.read_text(encoding="utf-8")
    text_de = readme_de.read_text(encoding="utf-8")

    assert len(text_en) >= 4000
    assert len(text_de) >= 4000
    assert "assets/banner.svg" in text_en and "assets/banner.svg" in text_de
    assert "README.de.md" in text_en
    assert "README.md" in text_de
    assert "docs/DESIGN.md" in text_en and "docs/DESIGN.md" in text_de
    assert "LICENSE" in text_en and "LICENSE" in text_de


def test_version_parity_across_repo() -> None:
    import cloudlockfixer

    version = cloudlockfixer.__version__
    assert version == "0.2.3"

    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{version}"' in pyproject_text

    llms_text = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
    assert f"Release version: {version}" in llms_text

    release_gate_text = (PROJECT_ROOT / "RELEASE_GATE.md").read_text(encoding="utf-8")
    assert f"Kanonische Source-Version:** `{version}`" in release_gate_text


def test_llms_txt_structure_and_timestamp() -> None:
    llms_path = PROJECT_ROOT / "llms.txt"
    assert llms_path.is_file(), "llms.txt must exist"
    text = llms_path.read_text(encoding="utf-8")

    assert text.startswith("# CloudLockFixer")
    assert "> Last-checked: 2026-09-10" in text
    assert "## Last-checked: 2026-09-10" in text
    assert "https://github.com/file-bricks/CloudLockFixer" in text


def test_mermaid_diagrams_syntax() -> None:
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    for text, name in [(readme_en, "README.md"), (readme_de, "README.de.md")]:
        assert "```mermaid" in text, f"Missing mermaid diagrams in {name}"
        assert "flowchart TD" in text, f"Missing flowchart diagram in {name}"
        assert "sequenceDiagram" in text, f"Missing sequence diagram in {name}"
        assert "cldflt" in text, f"Missing cldflt reference in {name}"
        assert "SHA-256" in text, f"Missing SHA-256 reference in {name}"


def test_sibling_ecosystem_and_urls() -> None:
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    required_siblings = [
        "file-bricks/SoftwareCenter",
        "file-bricks/knowledgedigest",
        "open-bricks",
        "ellmos-ai/system-auditor",
        "ellmos-ai/file-collect-sort-action",
        "dev-bricks/automizer-for-claude-desktop",
        "doc-bricks/USR_pic2pic",
        "doc-bricks/USR_PDFunlock",
    ]
    for sibling in required_siblings:
        assert sibling in readme_en, f"Missing sibling {sibling} in README.md"
        assert sibling in readme_de, f"Missing sibling {sibling} in README.de.md"


def test_quick_navigation_anchors() -> None:
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    assert "## Quick Navigation" in readme_en
    assert "## Schnellnavigation" in readme_de
    assert "(#interactive-architecture--lifecycle)" in readme_en
    assert "(#interaktive-architektur--lebenszyklus)" in readme_de
    assert "(#sibling-ecosystem-matrix)" in readme_en
    assert "(#geschwister-ökosystem-matrix)" in readme_de


def test_security_policy_supported_versions() -> None:
    sec_text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "| `0.2.x` | :white_check_mark: |" in sec_text
    assert "| `< 0.2.0` | :x: |" in sec_text
    assert "### Unterstützte Versionen" in sec_text
    assert "### Supported Versions" in sec_text


def test_gitignore_hygiene_patterns() -> None:
    """Ensure .gitignore enforces multi-host sync, lock and coverage hardening."""
    gi_path = PROJECT_ROOT / ".gitignore"
    assert gi_path.is_file(), ".gitignore must exist"
    gi_text = gi_path.read_text(encoding="utf-8")

    expected_patterns = [
        "*-WORKSTATION-LG*",
        "*-ASUS-GEI*",
        "*-WORKSTATION*",
        "*-conflict-*",
        "*.sync-conflict-*",
        "*.conflict",
        "*-CONFLIT-*",
        "*.sync-temp-*",
        "* (kopie)*",
        "* (copy)*",
        "LOCK",
        "LOCK.*",
        "*.lock",
        "LOCK*.txt",
        "LOCK.permissions.json",
        "uv.lock",
        ".coverage",
        ".coverage.*",
        "coverage/",
        "htmlcov/",
        ".ruff_cache/",
        "wheelhouse/",
        ".wheel-smoke/",
    ]
    for pat in expected_patterns:
        assert pat in gi_text, f"Missing pattern '{pat}' in .gitignore"


def test_pytest_configuration_and_flags() -> None:
    """Ensure pyproject.toml configures standardized pytest options."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    pytest_ini = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert pytest_ini.get("testpaths") == ["tests"]
    assert pytest_ini.get("pythonpath") == ["src"]
    assert pytest_ini.get("addopts") == "-ra -v"


def test_ci_workflow_pytest_flags() -> None:
    """Ensure CI workflow runs compileall and pytest with -ra -v."""
    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "tests.yml"
    assert workflow_path.is_file(), "tests.yml must exist"
    workflow_text = workflow_path.read_text(encoding="utf-8")

    assert "python -m compileall -q src tests" in workflow_text
    assert "python -m pytest -ra -v" in workflow_text


def test_changelog_recent_pfad_a_entry() -> None:
    """Ensure CHANGELOG.md records the current patch release and hygiene entry."""
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    assert changelog_path.is_file(), "CHANGELOG.md must exist"
    cl_text = changelog_path.read_text(encoding="utf-8")

    assert "## [0.2.3] - 2026-09-10" in cl_text
    assert "Pfad A" in cl_text
