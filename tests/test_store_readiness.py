"""Tests for scripts/check_store_readiness.py and Microsoft Store packaging contract."""

from __future__ import annotations

import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
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


def test_store_package_json_has_six_tier2_languages():
    data = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))
    langs = data.get("languages", [])
    expected = ["de-DE", "en-US", "es-ES", "zh-CN", "ja-JP", "ru-RU"]
    for lang in expected:
        assert lang in langs, f"Language {lang} missing in store_package.json"


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


def test_store_listing_has_tier2_six_languages():
    content = (PROJECT_ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")
    headings = ["## Deutsch", "## English", "## Español", "## 简体中文", "## 日本語", "## Русский"]
    for h in headings:
        assert h in content, f"Heading {h} missing in STORE_LISTING.md"

    kw_checks = [
        (r"### Schlüsselwörter[^\n]*\n+([^\n#]+)", "German"),
        (r"### Keywords[^\n]*\n+([^\n#]+)", "English"),
        (r"### Palabras clave[^\n]*\n+([^\n#]+)", "Spanish"),
        (r"### 关键词[^\n]*\n+([^\n#]+)", "Chinese"),
        (r"### キーワード[^\n]*\n+([^\n#]+)", "Japanese"),
        (r"### Ключевые слова[^\n]*\n+([^\n#]+)", "Russian"),
    ]
    for pattern, lang_name in kw_checks:
        m = re.search(pattern, content)
        assert m is not None, f"Keywords for {lang_name} not found in STORE_LISTING.md"
        kws = [k.strip() for k in m.group(1).split(",") if k.strip()]
        assert 1 <= len(kws) <= 7, f"{lang_name} keywords count invalid: {len(kws)}"
        for k in kws:
            assert len(k) <= 30, f"{lang_name} keyword '{k}' exceeds 30 chars"


def test_appx_manifest_structure():
    manifest_path = PROJECT_ROOT / "store_package" / "CloudLockFixer" / "AppxManifest.xml"
    assert manifest_path.is_file()
    content = manifest_path.read_text(encoding="utf-8")
    assert "runFullTrust" in content
    assert 'Executable="CloudLockFixer.exe"' in content
    assert f'Identity Name="{CANONICAL_IDENTITY}"' in content
    assert 'Square150x150Logo="icons\\icon_150x150.png"' in content
    assert 'Square44x44Logo="icons\\icon_44x44.png"' in content


def test_appx_manifest_has_six_tier2_languages():
    manifest_path = PROJECT_ROOT / "store_package" / "CloudLockFixer" / "AppxManifest.xml"
    content = manifest_path.read_text(encoding="utf-8")
    for lang in ("de-de", "en-us", "es-es", "zh-cn", "ja-jp", "ru-ru"):
        assert f'Language="{lang}"' in content, f"Resource language {lang} missing in AppxManifest.xml"


def test_releases_windowsstore_staging_complete():
    staging = PROJECT_ROOT / "releases" / "windowsstore"
    assert staging.is_dir()
    for req in (
        "BUILD.md",
        "WACK_PROTOCOL.md",
        "store_settings.json",
        "store_listing_de.md",
        "store_listing_en.md",
        "store_listing_es.md",
        "store_listing_zh.md",
        "store_listing_ja.md",
        "store_listing_ru.md",
        "StoreLogo.png",
    ):
        path = staging / req
        assert path.is_file(), f"Missing staging file: {req}"
        assert path.stat().st_size > 0

    # Verify WACK preflight reports
    report_dir = staging / "test_reports"
    assert report_dir.is_dir(), "test_reports directory must exist"
    xml_reports = list(report_dir.glob("wack_preflight_*.xml"))
    assert len(xml_reports) >= 1, "At least one WACK preflight XML report must exist"

    latest_xml = max(xml_reports, key=lambda p: p.stat().st_mtime)
    tree = ET.parse(latest_xml)
    root = tree.getroot()
    assert root.attrib.get("OverallResult") == "PASS"
    assert root.attrib.get("Application") == "CloudLockFixer"
    assert root.attrib.get("Identity") == CANONICAL_IDENTITY

    checks = root.findall("Check")
    assert len(checks) >= 6
    for c in checks:
        assert c.attrib.get("Result") == "PASS"

    json_report = latest_xml.with_suffix(".json")
    assert json_report.is_file(), "WACK preflight JSON companion must exist"
    data = json.loads(json_report.read_text(encoding="utf-8"))
    assert data.get("overall_result") == "PASS"
    assert data.get("summary", {}).get("fail_count") == 0

    # Verify store_settings.json keywords contract
    settings_data = json.loads((staging / "store_settings.json").read_text(encoding="utf-8"))
    kws_de = settings_data.get("keywords_de", [])
    assert isinstance(kws_de, list) and 1 <= len(kws_de) <= 7
    kws_en = settings_data.get("keywords_en", [])
    assert isinstance(kws_en, list) and 1 <= len(kws_en) <= 7

    # Verify WACK_PROTOCOL.md contents
    protocol_content = (staging / "WACK_PROTOCOL.md").read_text(encoding="utf-8")
    assert "PASS" in protocol_content
    assert CANONICAL_IDENTITY in protocol_content


def test_releases_windowsstore_staging_has_six_languages():
    staging = PROJECT_ROOT / "releases" / "windowsstore"
    for lang in ("de", "en", "es", "zh", "ja", "ru"):
        listing_file = staging / f"store_listing_{lang}.md"
        assert listing_file.is_file(), f"Missing staging listing: {listing_file.name}"
        assert listing_file.stat().st_size > 50

    settings_data = json.loads((staging / "store_settings.json").read_text(encoding="utf-8"))
    for lang in ("de", "en", "es", "zh", "ja", "ru"):
        kws = settings_data.get(f"keywords_{lang}", [])
        assert isinstance(kws, list) and 1 <= len(kws) <= 7, f"Missing or invalid keywords_{lang}"
        desc = settings_data.get(f"description_{lang}", "")
        assert isinstance(desc, str) and 1 <= len(desc) <= 100, f"description_{lang} out of bounds: {len(desc)}"
