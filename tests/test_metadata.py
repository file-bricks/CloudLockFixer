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
        "LLM Ready",
        "Marketing Log",
        "Third-Party Licenses",
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
    assert "> Last-checked: 2026-09-18" in text
    assert "## Last-checked: 2026-09-18" in text
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
    assert "(#2-architecture--system-design)" in readme_en or "(#interactive-architecture--lifecycle)" in readme_en
    assert "(#2-architektur--systemdesign)" in readme_de or "(#interaktive-architektur--lebenszyklus)" in readme_de
    assert "(#17-sibling-ecosystem-matrix)" in readme_en or "(#sibling-ecosystem-matrix)" in readme_en
    assert "(#17-geschwister-ökosystem-matrix)" in readme_de or "(#geschwister-ökosystem-matrix)" in readme_de


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


def test_ci_concurrency_and_timeout_guardrails() -> None:
    """Verify CI workflows have concurrency cancellation and explicit timeout-minutes."""
    workflow_dir = PROJECT_ROOT / ".github" / "workflows"
    workflows = {
        "tests.yml": 15,
        "source-platform-smoke.yml": 15,
        "stale.yml": 10,
        "welcome.yml": 5,
    }

    for wf_name, expected_timeout in workflows.items():
        wf_file = workflow_dir / wf_name
        assert wf_file.is_file(), f"Workflow {wf_name} missing"
        content = wf_file.read_text(encoding="utf-8")
        assert "concurrency:" in content, f"concurrency missing in {wf_name}"
        assert "cancel-in-progress: true" in content, f"cancel-in-progress missing in {wf_name}"
        assert f"timeout-minutes: {expected_timeout}" in content, (
            f"timeout-minutes: {expected_timeout} missing in {wf_name}"
        )


def test_gitignore_multihost_and_lock_defense() -> None:
    """Verify .gitignore includes multi-host, cloud conflict, and canonical lock patterns."""
    gitignore_file = PROJECT_ROOT / ".gitignore"
    assert gitignore_file.is_file(), ".gitignore must exist"
    content = gitignore_file.read_text(encoding="utf-8")

    patterns = [
        "*conflicted copy*",
        "* (Kopie)*",
        "* (Copy)*",
        "*-WORKSTATION*",
        "*-ASUS*",
        "*-LAPTOP*",
        "*-Mac Studio*",
        "LOCK",
        "*.lock",
        "uv.lock",
        "!package-lock.json",
        "*.orig",
        "*.rej",
        ".coverage.*",
        ".hypothesis/",
        ".turbo/",
        ".nyc_output/",
    ]
    for pattern in patterns:
        assert pattern in content, f"Pattern {pattern} missing in .gitignore"


def test_marketing_log_recent_hygiene_entry() -> None:
    """Verify MARKETING-LOG.txt exists, is up-to-date, and documents governance invariants."""
    mktg_file = PROJECT_ROOT / "MARKETING-LOG.txt"
    assert mktg_file.is_file(), "MARKETING-LOG.txt must exist"
    content = mktg_file.read_text(encoding="utf-8")

    assert "Stand: 2026-09-18" in content, "Recent audit date missing in MARKETING-LOG.txt"
    assert "CLOUDLOCKFIXER SUITE" in content
    assert "INV-LOCAL-01" in content and "INV-SLA-10" in content, "Governance pillars missing in MARKETING-LOG.txt"
    assert "Pfad A" in content or "PFAD A" in content, "Pfad A maintenance section missing in MARKETING-LOG.txt"
    assert "Pfad B" in content or "PFAD B" in content, "Pfad B marketing audit section missing in MARKETING-LOG.txt"


def test_quick_navigation_18_points_parity() -> None:
    """Verify README.md and README.de.md have identical 18-point navigation and reciprocal anchors."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    for i in range(1, 19):
        assert f"{i}. [" in readme_en, f"Missing point {i} in README.md Quick Navigation"
        assert f"{i}. [" in readme_de, f"Missing point {i} in README.de.md Schnellnavigation"

    required_anchors = [
        "1-features",
        "2-architecture",
        "3-target-personas--discoverability",
        "4-comparative-matrix-vs-alternatives",
        "5-dual-mermaid-diagrams",
        "6-governance--runtime-invariants",
        "7-multi-cloud-provider-support",
        "8-cryptographic-copydelete-fallback",
        "9-atomic-multi-step-chains",
        "10-visual-showcase--gui-workflow",
        "11-installation--quickstart",
        "12-cli--automation-usage",
        "13-queue-file-queuetxt-integration",
        "14-cross-platform-parity",
        "15-testing--quality-verification",
        "16-third-party-licenses--transparency",
        "17-sibling-ecosystem-matrix",
        "18-security-policy--statutory-notice",
    ]
    for anchor in required_anchors:
        assert f'id="{anchor}"' in readme_en, f"Anchor id='{anchor}' missing in README.md"
        assert f'id="{anchor}"' in readme_de, f"Anchor id='{anchor}' missing in README.de.md"


def test_target_personas_and_high_intent_queries() -> None:
    """Verify target personas and SEO search queries across READMEs and MARKETING-LOG.txt."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")
    mktg_log = (PROJECT_ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    for persona in ["[PERSONA-01]", "[PERSONA-02]", "[PERSONA-03]", "[PERSONA-04]"]:
        assert persona in readme_en, f"Persona {persona} missing in README.md"
        assert persona in readme_de, f"Persona {persona} missing in README.de.md"
        assert persona in mktg_log, f"Persona {persona} missing in MARKETING-LOG.txt"

    assert "onedrive file locked" in readme_en.lower()
    assert "cldflt" in readme_en.lower()
    assert "onedrive datei gesperrt" in readme_de.lower()


def test_comparative_matrix_vs_alternatives() -> None:
    """Verify 10-dimension comparative matrix vs alternatives in README.md and README.de.md."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    for text, name in [(readme_en, "README.md"), (readme_de, "README.de.md")]:
        assert "LockHunter" in text, f"Missing LockHunter alternative in {name}"
        assert "INV-LOCAL-01" in text, f"Missing INV-LOCAL-01 mapping in {name}"
        assert "INV-HASH-03" in text, f"Missing INV-HASH-03 mapping in {name}"
        assert "INV-SLA-10" in text, f"Missing INV-SLA-10 mapping in {name}"


def test_dual_mermaid_diagrams() -> None:
    """Verify dual Mermaid diagrams (flowchart TD and sequenceDiagram) in both READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")

    for text, name in [(readme_en, "README.md"), (readme_de, "README.de.md")]:
        assert "flowchart TD" in text, f"Missing flowchart TD in {name}"
        assert "sequenceDiagram" in text, f"Missing sequenceDiagram in {name}"
        assert "autonumber" in text, f"Missing autonumber in {name} sequenceDiagram"
        assert "cldflt" in text, f"Missing cldflt in {name}"
        assert "SHA-256" in text, f"Missing SHA-256 in {name}"


def test_third_party_licenses_md_integrity() -> None:
    """Verify THIRD_PARTY_LICENSES.md exists, documents PySide6 LGPL-3.0, and has zero-copyleft audit."""
    license_file = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert license_file.is_file(), "THIRD_PARTY_LICENSES.md must exist"
    content = license_file.read_text(encoding="utf-8")

    assert "Software Bill of Materials (SBOM)" in content
    assert "PySide6" in content and "LGPL-3.0-only" in content
    assert "shiboken6" in content
    assert "pytest" in content and "MIT" in content
    assert "ruff" in content
    assert "PyInstaller" in content
    assert "RunAsInvoker" in content
    assert "Zero-Copyleft" in content
    assert "INV-LOCAL-01" in content and "INV-SLA-10" in content


def test_german_statutory_notice() -> None:
    """Verify German statutory notice (§ 521 BGB Gefälligkeitsrecht) in README.de.md."""
    readme_de = (PROJECT_ROOT / "README.de.md").read_text(encoding="utf-8")
    assert "§ 521 BGB" in readme_de
    assert "Gefälligkeitsrecht" in readme_de


def test_changelog_recent_pfad_b_entry() -> None:
    """Verify CHANGELOG.md contains the 2026-09-18 Pfad B audit entry."""
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Pfad B" in changelog
    assert "2026-09-18" in changelog
