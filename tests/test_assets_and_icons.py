from __future__ import annotations

import json
from pathlib import Path
import struct

from PIL import Image

PROJ_ROOT = Path(__file__).resolve().parents[1]


def _read_ico_sizes(ico_path: Path) -> list[tuple[int, int]]:
    with open(ico_path, "rb") as f:
        reserved, ico_type, count = struct.unpack("<HHH", f.read(6))
        assert ico_type == 1, "Not an ICO file"
        sizes = []
        for _ in range(count):
            w, h, _colors, _res, _planes, _bpp, _size, _offset = struct.unpack("<BBBBHHII", f.read(16))
            sizes.append((w or 256, h or 256))
        return sizes


def test_master_icons_exist() -> None:
    desktop_png = PROJ_ROOT / "DesktopIcon.png"
    icon_png = PROJ_ROOT / "icon.png"
    ico_file = PROJ_ROOT / "CloudLockFixer.ico"
    desktop_ico = PROJ_ROOT / "DesktopIcon.ico"

    assert desktop_png.exists(), "DesktopIcon.png must exist"
    assert icon_png.exists(), "icon.png must exist"
    assert ico_file.exists(), "CloudLockFixer.ico must exist"
    assert desktop_ico.exists(), "DesktopIcon.ico must exist"

    with Image.open(desktop_png) as img:
        assert img.size == (1024, 1024), "DesktopIcon.png must be 1024x1024"

    with Image.open(icon_png) as img:
        assert img.size == (1024, 1024), "icon.png must be 1024x1024"

    sizes = _read_ico_sizes(ico_file)
    assert len(sizes) == 7, f"CloudLockFixer.ico must have 7 layers, got {len(sizes)}"
    assert (16, 16) in sizes and (32, 32) in sizes and (256, 256) in sizes


def test_resources_folder_parity() -> None:
    res_dir = PROJ_ROOT / "resources"
    ico_file = res_dir / "icon.ico"
    preview_png = res_dir / "icon_preview.png"

    assert ico_file.exists(), "resources/icon.ico must exist"
    assert preview_png.exists(), "resources/icon_preview.png must exist"

    with Image.open(preview_png) as img:
        assert img.size == (1024, 1024), "icon_preview.png must be 1024x1024"

    sizes = _read_ico_sizes(ico_file)
    assert len(sizes) == 7, "resources/icon.ico must have 7 layers"


def test_assets_folder_parity() -> None:
    assets_dir = PROJ_ROOT / "assets"
    assert assets_dir.exists(), "assets directory must exist"

    icon_png = assets_dir / "icon.png"
    icon_ico = assets_dir / "icon.ico"
    favicon_png = assets_dir / "favicon.png"
    favicon_ico = assets_dir / "favicon.ico"

    assert icon_png.exists()
    assert icon_ico.exists()
    assert favicon_png.exists()
    assert favicon_ico.exists()

    with Image.open(favicon_png) as img:
        assert img.size == (32, 32)

    fav_sizes = _read_ico_sizes(favicon_ico)
    assert (16, 16) in fav_sizes and (32, 32) in fav_sizes


def test_mobile_pwa_icons_and_manifest() -> None:
    mobile_dir = PROJ_ROOT / "mobile_icons"
    assert mobile_dir.exists(), "mobile_icons directory must exist"

    required_files = [
        "icon.png",
        "icon-192.png",
        "icon-512.png",
        "icon-maskable-192.png",
        "icon-maskable-512.png",
        "apple-touch-icon.png",
        "favicon.png",
        "favicon.ico",
        "manifest.json",
    ]
    for filename in required_files:
        path = mobile_dir / filename
        assert path.exists(), f"mobile_icons/{filename} missing"

    with Image.open(mobile_dir / "icon-192.png") as img:
        assert img.size == (192, 192)
    with Image.open(mobile_dir / "icon-512.png") as img:
        assert img.size == (512, 512)
    with Image.open(mobile_dir / "icon-maskable-192.png") as img:
        assert img.size == (192, 192)
    with Image.open(mobile_dir / "icon-maskable-512.png") as img:
        assert img.size == (512, 512)
    with Image.open(mobile_dir / "apple-touch-icon.png") as img:
        assert img.size == (180, 180)

    # Verify manifest.json
    manifest_path = mobile_dir / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "CloudLockFixer"
    assert len(data["icons"]) >= 4
    for icon_entry in data["icons"]:
        icon_file = mobile_dir / icon_entry["src"]
        assert icon_file.exists(), f"Icon referenced in manifest does not exist: {icon_entry['src']}"


def test_store_assets() -> None:
    store_dir = PROJ_ROOT / "store_assets"
    assert store_dir.exists(), "store_assets directory must exist"

    sizes = {
        "icon_44x44.png": (44, 44),
        "icon_50x50.png": (50, 50),
        "icon_150x150.png": (150, 150),
        "icon_310x150.png": (310, 150),
        "icon_310x310.png": (310, 310),
    }
    for filename, expected_size in sizes.items():
        file_path = store_dir / filename
        assert file_path.exists(), f"store_assets/{filename} missing"
        with Image.open(file_path) as img:
            assert img.size == expected_size, f"{filename} has size {img.size}, expected {expected_size}"
