"""Tests for scripts/check_store_readiness.py and Microsoft Store packaging contract."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_store_readiness import (  # noqa: E402
    PNG_SIGNATURE,
    REQUIRED_DOCUMENTS,
    REQUIRED_TILE_ICONS,
    validate_store_readiness,
)

CANONICAL_PUBLISHER = "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
CANONICAL_IDENTITY = "Geiger.CloudLockFixer"


def test_full_store_readiness_check_passes():
    result = validate_store_readiness(PROJECT_ROOT)
    assert result["status"] == "PASS", f"Store readiness failed: {result}"
    assert result["repository_clean"] is True
    assert result["repository_findings"] == []


def test_required_documents_exist():
    for doc in REQUIRED_DOCUMENTS:
        path = PROJECT_ROOT / doc
        assert path.is_file(), f"Required document missing: {doc}"
        content = path.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, f"Document too short: {doc}"


def test_store_package_json_contract():
    data = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))
    assert data.get("publisher") == CANONICAL_PUBLISHER
    assert data.get("publisher_display") == "Geiger"
    assert data.get("identity_name") == CANONICAL_IDENTITY
    assert data.get("capabilities") == "runFullTrust" or "runFullTrust" in data.get("capabilities", [])
    assert data.get("executable") == "CloudLockFixer.exe"
    assert data.get("license") == "MIT"
    assert "de-DE" in data.get("languages", [])
    assert "en-US" in data.get("languages", [])
    assert data.get("privacy_url", "").startswith("https://")
    assert data.get("support_url", "").startswith("https://")


def test_store_icons_match_specification():
    for name, req_w, req_h in REQUIRED_TILE_ICONS:
        for folder in (
            PROJECT_ROOT / "store_assets",
            PROJECT_ROOT / "store_package" / "CloudLockFixer" / "icons",
            PROJECT_ROOT / "releases" / "windowsstore",
        ):
            icon_path = folder / name
            assert icon_path.is_file(), f"Icon {name} missing in {folder}"
            raw = icon_path.read_bytes()
            assert raw.startswith(PNG_SIGNATURE), f"{name} is not a valid PNG in {folder}"
            w, h = struct.unpack(">II", raw[16:24])
            if name != "StoreLogo.png":
                assert (w, h) == (req_w, req_h), f"{name}: expected ({req_w}, {req_h}), got ({w}, {h})"
            else:
                assert (w, h) == (50, 50), f"StoreLogo.png expected (50, 50), got ({w}, {h})"


def test_store_screenshots_match_aspect_ratio():
    shot_dir = PROJECT_ROOT / "releases" / "windowsstore" / "screenshots"
    assert shot_dir.is_dir()
    shots = list(shot_dir.glob("*.png"))
    assert len(shots) >= 3, f"Expected at least 3 screenshots, found {len(shots)}"

    for shot in shots:
        raw = shot.read_bytes()
        assert raw.startswith(PNG_SIGNATURE)
        w, h = struct.unpack(">II", raw[16:24])
        assert w >= 1366, f"{shot.name}: width {w} < 1366"
        assert h >= 768, f"{shot.name}: height {h} < 768"
        assert round(w / h, 2) == 1.78, f"{shot.name}: not 16:9 ratio ({w}x{h})"


def test_partner_center_10_1_3_keywords_max_7():
    content = (PROJECT_ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")

    de_match = re.search(r"### Schlüsselwörter[^\n]*\n+([^\n#]+)", content)
    assert de_match is not None, "German keywords heading not found"
    de_kws = [k.strip() for k in de_match.group(1).split(",") if k.strip()]
    assert 1 <= len(de_kws) <= 7, f"German keywords count out of bounds: {len(de_kws)}"
    for k in de_kws:
        assert len(k) <= 30, f"Keyword too long: '{k}'"

    en_match = re.search(r"### Keywords[^\n]*\n+([^\n#]+)", content)
    assert en_match is not None, "English keywords heading not found"
    en_kws = [k.strip() for k in en_match.group(1).split(",") if k.strip()]
    assert 1 <= len(en_kws) <= 7, f"English keywords count out of bounds: {len(en_kws)}"
    for k in en_kws:
        assert len(k) <= 30, f"Keyword too long: '{k}'"


def test_appx_manifest_structure():
    manifest_path = PROJECT_ROOT / "store_package" / "CloudLockFixer" / "AppxManifest.xml"
    assert manifest_path.is_file()
    content = manifest_path.read_text(encoding="utf-8")
    assert "runFullTrust" in content
    assert 'Executable="CloudLockFixer.exe"' in content
    assert f'Identity Name="{CANONICAL_IDENTITY}"' in content
    assert 'Square150x150Logo="icons\\icon_150x150.png"' in content
    assert 'Square44x44Logo="icons\\icon_44x44.png"' in content


def test_releases_windowsstore_staging_complete():
    staging = PROJECT_ROOT / "releases" / "windowsstore"
    assert staging.is_dir()
    for req in (
        "BUILD.md",
        "WACK_PROTOCOL.md",
        "store_settings.json",
        "store_listing_de.md",
        "store_listing_en.md",
        "StoreLogo.png",
    ):
        path = staging / req
        assert path.is_file(), f"Missing staging file: {req}"
        assert path.stat().st_size > 0
