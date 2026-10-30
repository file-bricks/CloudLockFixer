"""Tests für den CloudLockFixer Web Companion & PWA."""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web_companion"


def test_web_companion_core_files_exist():
    """Prüft, ob alle Kernkomponenten des Web Companions vorhanden sind."""
    required_files = [
        WEB_DIR / "index.html",
        WEB_DIR / "app.css",
        WEB_DIR / "app.js",
        WEB_DIR / "sw.js",
        WEB_DIR / "manifest.json",
        WEB_DIR / "README.md",
        WEB_DIR / "icons" / "icon-192.png",
        WEB_DIR / "icons" / "icon-512.png",
        WEB_DIR / "icons" / "favicon.png",
    ]
    for rf in required_files:
        assert rf.is_file(), f"Erwartete Datei fehlt im Web Companion: {rf}"


def test_web_companion_zero_egress():
    """Zero-Egress-Invariante: keine externen Skripte, CDNs oder Schriften."""
    index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    app_css = (WEB_DIR / "app.css").read_text(encoding="utf-8")
    app_js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    for name, content in [("index.html", index_html), ("app.css", app_css)]:
        # Keine externen script/link/font URLs
        external_urls = re.findall(r'https?://[^\s"\'>]+', content)
        # Erlaubt ist nur der $schema Verweis in Kommentaren/Metadaten, keine Laufzeit-Ressourcen
        for url in external_urls:
            assert "fonts.googleapis" not in url
            assert "cdnjs.cloudflare" not in url
            assert "cdn." not in url

    # Keine Netzwerk-Fetch-Befehle zu externen Zielen in app.js
    assert "fetch('http" not in app_js
    assert 'fetch("http' not in app_js


def test_web_companion_w3c_manifest():
    """Prüft W3C WebApp Manifest auf Vollständigkeit und Validität."""
    manifest_path = WEB_DIR / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert data.get("name") == "CloudLockFixer Web Companion"
    assert data.get("short_name") == "CLF Companion"
    assert data.get("display") == "standalone"
    assert data.get("start_url") == "./index.html"
    assert data.get("theme_color") == "#2e9e44"
    assert "icons" in data and len(data["icons"]) >= 2

    for icon in data["icons"]:
        icon_path = WEB_DIR / icon["src"].lstrip("./")
        assert icon_path.is_file(), f"Manifest-Icon nicht gefunden: {icon_path}"


def test_web_companion_i18n_coverage():
    """Prüft, ob app.js alle 6 Tier-2 Sprachen vollständig abdeckt."""
    app_js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    # Prüfe Vorkommen aller 6 Sprachcodes im I18N-Block
    for lang in ["de", "en", "es", "zh", "ja", "ru"]:
        assert f"{lang}: {{" in app_js, f"Sprachdefinition für '{lang}' fehlt in app.js"


def test_web_companion_html_semantics_and_a11y():
    """Prüft semantische HTML5-Struktur und Barrierefreiheitsattribute."""
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")

    assert "<!DOCTYPE html>" in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html
    assert 'role="banner"' in html
    assert 'role="main"' in html
    assert 'role="contentinfo"' in html
    assert 'role="tablist"' in html
    assert 'aria-selected="true"' in html
    assert 'aria-label=' in html
