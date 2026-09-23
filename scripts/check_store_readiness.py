"""Validate repository-owned and external Windows Store readiness materials for CloudLockFixer.

Repository-owned materials are checked in ``project_root``. Build and review
evidence can be supplied explicitly via ``--evidence-root`` for full release gate validation.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import tomllib
import zipfile
from pathlib import Path
from typing import Sequence

REQUIRED_DOCUMENTS = (
    "PRIVACY_POLICY.md",
    "SUPPORT.md",
    "STORE_LISTING.md",
    "WINDOWS_STORE_PREP.md",
    "THIRD_PARTY_LICENSES.md",
)

PASS_MARKERS = {
    "fulltrust-review.txt": "STATUS: PASS",
    "windows-tray-smoke.txt": "STATUS: PASS",
    "live-url-readback.txt": "STATUS: PASS",
    "msix-signature.txt": "SIGNATURE STATUS: PASS",
    "wack-report.txt": "OVERALL RESULT: PASS",
}

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

REQUIRED_TILE_ICONS = (
    ("icon_44x44.png", 44, 44),
    ("icon_50x50.png", 50, 50),
    ("icon_150x150.png", 150, 150),
    ("icon_310x150.png", 310, 150),
    ("icon_310x310.png", 310, 310),
    ("StoreLogo.png", 50, 50),
)


def _read_nonempty(path: Path) -> str | None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return content if content.strip() else None


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _project_version(project_root: Path) -> str | None:
    try:
        data = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        pass
    else:
        project = data.get("project")
        if isinstance(project, dict):
            version = project.get("version")
            if isinstance(version, str) and version:
                return version
    return None


def _read_png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
        if not data.startswith(PNG_SIGNATURE) or len(data) < 24:
            return None
        w, h = struct.unpack(">II", data[16:24])
        return (w, h)
    except OSError:
        return None


def _check_repository(project_root: Path) -> list[str]:
    findings: list[str] = []
    config_path = project_root / "store_package.json"
    config = _load_json(config_path)
    if config is None:
        findings.append("[repository] store_package.json is missing or invalid")
    else:
        for field in ("publisher", "publisher_display", "identity_name", "version", "executable", "license"):
            if not isinstance(config.get(field), str) or not str(config[field]).strip():
                findings.append(f"[repository] store_package.json field {field!r} is missing")

        languages = config.get("languages")
        if not isinstance(languages, list) or not languages:
            findings.append("[repository] store_package.json field 'languages' is missing or empty")

        app_name = config.get("name") or config.get("app_name")
        if not isinstance(app_name, str) or not app_name.strip():
            findings.append("[repository] store_package.json name/app_name is missing")

        for field in ("publisher", "publisher_display", "identity_name"):
            value = str(config.get(field, ""))
            if "your" in value.lower() or "placeholder" in value.lower():
                findings.append(f"[repository] store_package.json contains placeholder: {field}")

        for field in ("privacy_url", "support_url"):
            value = config.get(field)
            if not isinstance(value, str) or not value.startswith("https://"):
                findings.append(
                    f"[repository] store_package.json field {field!r} needs an HTTPS URL"
                )

        capabilities = config.get("capabilities")
        if isinstance(capabilities, list):
            if "runFullTrust" not in capabilities:
                findings.append("[repository] store_package.json must declare runFullTrust")
        elif isinstance(capabilities, str):
            if "runFullTrust" not in capabilities:
                findings.append("[repository] store_package.json must declare runFullTrust")
        else:
            findings.append("[repository] store_package.json capabilities missing or invalid")

        project_ver = _project_version(project_root)
        store_ver = str(config.get("version", ""))
        if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", store_ver):
            findings.append("[repository] store_package.json version must have 4 numeric parts")
        elif project_ver is not None and not store_ver.startswith(project_ver):
            findings.append(
                f"[repository] version mismatch: project={project_ver}, store={store_ver}"
            )

    manifests = sorted((project_root / "store_package").glob("**/AppxManifest.xml"))
    if not manifests:
        findings.append("[repository] AppxManifest.xml is missing below store_package")
    else:
        manifest = _read_nonempty(manifests[0])
        if manifest is None:
            findings.append("[repository] AppxManifest.xml is empty or unreadable")
        else:
            for token, label in (
                ("runFullTrust", "runFullTrust capability"),
                ("Executable=", "application executable"),
                ("Version=", "package version"),
                ("Identity Name=", "package identity name"),
                ("Square150x150Logo=", "Square150x150Logo"),
                ("Square44x44Logo=", "Square44x44Logo"),
            ):
                if token not in manifest:
                    findings.append(f"[repository] AppxManifest.xml lacks {label}")

    for name in REQUIRED_DOCUMENTS:
        doc_path = project_root / name
        content = _read_nonempty(doc_path)
        if content is None:
            findings.append(f"[repository] {name} is missing or empty")
        elif name in ("STORE_LISTING.md", "SUPPORT.md"):
            for heading in ("Deutsch", "English"):
                if heading not in content:
                    findings.append(f"[repository] {name} lacks heading {heading}")

    license_content = _read_nonempty(project_root / "LICENSE")
    if license_content is None or "MIT" not in license_content:
        findings.append("[repository] LICENSE is missing or does not mention MIT")

    readme_content = _read_nonempty(project_root / "README.md")
    if readme_content is None or "PRIVACY_POLICY.md" not in readme_content:
        findings.append("[repository] README.md does not reference PRIVACY_POLICY.md")

    # Check Store Listing keywords according to Policy 10.1.3 (max 7 per language)
    listing_content = _read_nonempty(project_root / "STORE_LISTING.md")
    if listing_content:
        de_match = re.search(r"### Schlüsselwörter\s*\n+([^\n#]+)", listing_content)
        if de_match:
            de_kw = [k.strip() for k in de_match.group(1).split(",") if k.strip()]
            if len(de_kw) > 7:
                findings.append(
                    f"[repository] STORE_LISTING.md German keywords exceed Policy 10.1.3 limit (max 7, found {len(de_kw)})"
                )
        en_match = re.search(r"### Keywords\s*\n+([^\n#]+)", listing_content)
        if en_match:
            en_kw = [k.strip() for k in en_match.group(1).split(",") if k.strip()]
            if len(en_kw) > 7:
                findings.append(
                    f"[repository] STORE_LISTING.md English keywords exceed Policy 10.1.3 limit (max 7, found {len(en_kw)})"
                )

    # Verify tile icons across store_assets, store_package and releases/windowsstore
    for icon_name, expected_w, expected_h in REQUIRED_TILE_ICONS:
        for check_dir in (
            project_root / "store_assets",
            project_root / "store_package" / "CloudLockFixer" / "icons",
            project_root / "releases" / "windowsstore",
        ):
            icon_file = check_dir / icon_name
            if not icon_file.is_file():
                findings.append(f"[repository] tile icon missing: {check_dir.name}/{icon_name}")
            else:
                dims = _read_png_dimensions(icon_file)
                if dims is None:
                    findings.append(f"[repository] tile icon invalid PNG: {check_dir.name}/{icon_name}")
                elif dims != (expected_w, expected_h) and icon_name != "StoreLogo.png":
                    findings.append(
                        f"[repository] tile icon {check_dir.name}/{icon_name} dimension mismatch: expected ({expected_w}, {expected_h}), found {dims}"
                    )

    # Check store screenshots
    screenshot_dirs = [
        project_root / "releases" / "windowsstore" / "screenshots",
        project_root / "screenshots" / "store",
        project_root / "README" / "screenshots" / "store",
    ]
    screenshots = []
    for sdir in screenshot_dirs:
        if sdir.is_dir():
            for path in sdir.glob("*.png"):
                try:
                    if path.is_file() and path.read_bytes().startswith(PNG_SIGNATURE):
                        screenshots.append(path)
                except OSError:
                    continue

    if len(screenshots) < 3:
        findings.append(
            f"[repository] at least 3 valid PNG Store screenshots required; found {len(screenshots)}"
        )

    # Check releases/windowsstore/ staging files
    win_store_dir = project_root / "releases" / "windowsstore"
    if not win_store_dir.is_dir():
        findings.append("[repository] releases/windowsstore directory is missing")
    else:
        for req_name in ("BUILD.md", "WACK_PROTOCOL.md", "store_settings.json", "store_listing_de.md", "store_listing_en.md", "StoreLogo.png"):
            if not (win_store_dir / req_name).is_file():
                findings.append(f"[repository] releases/windowsstore lacks {req_name}")

    return findings


def _check_evidence(evidence_root: Path | None) -> list[str]:
    if evidence_root is None:
        return [
            "[external] evidence root was not supplied (Partner Center reservation, FullTrust review, "
            "Windows tray smoke, live URL readback, signed MSIX/hash, and WACK PASS remain open)"
        ]
    if not evidence_root.is_dir():
        return [f"[external] evidence root does not exist: {evidence_root}"]

    findings: list[str] = []
    for name, marker in PASS_MARKERS.items():
        content = _read_nonempty(evidence_root / name)
        if content is None or marker not in content:
            findings.append(f"[external] {name} is missing or lacks {marker!r}")

    return findings


def _validate_msix_archive(msix_path: Path, expected_version: str | None = None) -> list[str]:
    findings: list[str] = []
    if not msix_path.is_file():
        return [f"[msix] file does not exist: {msix_path}"]

    try:
        with zipfile.ZipFile(msix_path, "r") as zf:
            names = set(zf.namelist())
            for req in ("AppxManifest.xml", "AppxBlockMap.xml", "[Content_Types].xml"):
                if req not in names:
                    findings.append(f"[msix] archive lacks required package file: {req}")

            # Verify executable is present
            if not any(n.lower().endswith("cloudlockfixer.exe") for n in names):
                findings.append("[msix] archive lacks CloudLockFixer.exe")

            if "AppxManifest.xml" in names:
                manifest_xml = zf.read("AppxManifest.xml").decode("utf-8", errors="replace")
                if "runFullTrust" not in manifest_xml:
                    findings.append("[msix] AppxManifest inside MSIX lacks runFullTrust capability")
                if expected_version:
                    m = re.search(r'Version="([^"]+)"', manifest_xml)
                    if not m:
                        findings.append("[msix] AppxManifest inside MSIX lacks Version attribute")
                    elif m.group(1) != expected_version:
                        findings.append(
                            f"[msix] AppxManifest version mismatch: expected {expected_version}, found {m.group(1)}"
                        )
    except zipfile.BadZipFile:
        findings.append(f"[msix] file is not a valid zip/MSIX archive: {msix_path}")

    return findings


def validate_store_readiness(
    project_root: Path,
    evidence_root: Path | None = None,
    msix_path: Path | None = None,
) -> dict[str, object]:
    repo_findings = _check_repository(project_root)
    external_findings = _check_evidence(evidence_root)
    msix_findings = []
    if msix_path is not None:
        cfg = _load_json(project_root / "store_package.json")
        exp_ver = str(cfg.get("version", "")) if cfg else None
        msix_findings = _validate_msix_archive(msix_path, exp_ver)

    return {
        "status": "PASS" if (not repo_findings and not msix_findings) else "FINDINGS",
        "repository_clean": len(repo_findings) == 0,
        "repository_findings": repo_findings,
        "external_findings": external_findings,
        "msix_findings": msix_findings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Windows Store readiness for CloudLockFixer")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--msix", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = validate_store_readiness(args.project_root, args.evidence_root, args.msix)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Store Readiness Audit: {results['status']}")
        if results["repository_findings"]:
            print("\nRepository Findings:")
            for f in results["repository_findings"]:
                print(f"  - {f}")
        else:
            print("\n[OK] Repository-owned Store materials are 100% complete and valid.")

        if args.evidence_root:
            if results["external_findings"]:
                print("\nExternal Evidence Findings:")
                for f in results["external_findings"]:
                    print(f"  - {f}")
            else:
                print("\n[OK] External evidence passed.")

        if args.msix:
            if results["msix_findings"]:
                print("\nMSIX Archive Findings:")
                for f in results["msix_findings"]:
                    print(f"  - {f}")
            else:
                print("\n[OK] MSIX archive validated successfully.")

    return 0 if results["repository_clean"] and not results["msix_findings"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
