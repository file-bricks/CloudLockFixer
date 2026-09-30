"""Store screenshot generator for CloudLockFixer.

Generates 4 high-resolution 16:9 presentation screenshots (1920x1080)
for the Microsoft Partner Center and repository documentation:
1. 01_tray-queue-management.png
2. 02_multicloud-provider-support.png
3. 03_preventive-watcher-settings.png
4. 04_cross-platform-architecture.png
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

BG_COLOR = (244, 247, 251)
CARD_BG = (255, 255, 255)
CARD_BORDER = (222, 228, 238)
PRIMARY_COLOR = (37, 99, 235)      # Blue accent
SECONDARY_COLOR = (16, 185, 129)   # Emerald green
WARNING_COLOR = (245, 158, 11)     # Amber
TEXT_DARK = (15, 23, 42)          # Slate 900
TEXT_MUTED = (100, 116, 139)       # Slate 500
HEADER_BG = (255, 255, 255)
HEADER_BORDER = (226, 232, 240)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidate_fonts = [
        "C:\\Windows\\Fonts\\segoeui.ttf" if not bold else "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arial.ttf" if not bold else "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for font_path in candidate_fonts:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw_header(draw: ImageDraw.ImageDraw, canvas: Image.Image, title: str, subtitle: str, icon_img: Image.Image | None) -> None:
    draw.rectangle([0, 0, CANVAS_WIDTH, 140], fill=HEADER_BG)
    draw.line([0, 140, CANVAS_WIDTH, 140], fill=HEADER_BORDER, width=2)

    x_offset = 60
    if icon_img is not None:
        resized_icon = icon_img.resize((84, 84), Image.Resampling.LANCZOS)
        canvas.paste(resized_icon, (x_offset, 28), mask=resized_icon if resized_icon.mode == "RGBA" else None)
        x_offset += 105

    font_title = _get_font(34, bold=True)
    font_sub = _get_font(20, bold=False)

    draw.text((x_offset, 34), title, fill=TEXT_DARK, font=font_title)
    draw.text((x_offset, 82), subtitle, fill=TEXT_MUTED, font=font_sub)

    # Brand badge
    font_badge = _get_font(16, bold=True)
    badge_text = "Microsoft Store Edition"
    draw.rounded_rectangle([CANVAS_WIDTH - 300, 48, CANVAS_WIDTH - 60, 92], radius=8, fill=(238, 242, 255), outline=PRIMARY_COLOR, width=1)
    draw.text((CANVAS_WIDTH - 280, 58), badge_text, fill=PRIMARY_COLOR, font=font_badge)


def _draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, subtitle: str = "") -> None:
    draw.rounded_rectangle(box, radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    font_card_title = _get_font(22, bold=True)
    draw.text((box[0] + 30, box[1] + 25), title, fill=TEXT_DARK, font=font_card_title)
    if subtitle:
        font_card_sub = _get_font(16, bold=False)
        draw.text((box[0] + 30, box[1] + 60), subtitle, fill=TEXT_MUTED, font=font_card_sub)
        draw.line([box[0] + 30, box[1] + 95, box[2] - 30, box[1] + 95], fill=CARD_BORDER, width=1)
    else:
        draw.line([box[0] + 30, box[1] + 65, box[2] - 30, box[1] + 65], fill=CARD_BORDER, width=1)


def generate_frame_1(icon_img: Image.Image | None) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, canvas, "CloudLockFixer — Tray-Steuerung & Aufgaben-Warteschlange", "Verzögerte Umbenennungen, Verschiebungen und Löschungen für gesperrte Cloud-Dateien", icon_img)

    # Left card: Active Queue Overview
    _draw_card(draw, (60, 180, 1160, 1020), "Aktive Warteschlange (queue.json / queue.txt)", "3 Aufgaben erfasst • Nächster automatischer Durchlauf in 42 Minuten")

    font_item_title = _get_font(18, bold=True)
    font_item_sub = _get_font(15, bold=False)
    font_badge = _get_font(14, bold=True)

    items = [
        ("DONE", SECONDARY_COLOR, "delete  \"C:\\Users\\Lukas\\OneDrive\\Projekt\\temp_cache.lock\"", "Provider: OneDrive • copy+delete Workaround verifiziert • Quelldatei sicher entfernt"),
        ("DONE", SECONDARY_COLOR, "rename  \"C:\\Users\\Lukas\\Dropbox\\Kundenbericht_v1.docx\" -> \"Kundenbericht_final.docx\"", "Provider: Dropbox • Handle nach Sync-Zyklus freigegeben • Umbenennung erfolgreich"),
        ("PENDING", WARNING_COLOR, "move    \"C:\\Users\\Lukas\\GoogleDrive\\Export_2026.csv\" -> \"Archiv\\Export_2026.csv\"", "Provider: Google Drive (Virtual Mount) • Task wartet auf Freigabe • Keine Unterbrechung"),
    ]

    y = 300
    for status, color, cmd, desc in items:
        draw.rounded_rectangle([90, y, 1130, y + 105], radius=8, fill=(248, 250, 252), outline=CARD_BORDER, width=1)
        # Badge
        draw.rounded_rectangle([110, y + 18, 210, y + 50], radius=6, fill=color)
        draw.text((125, y + 24), status, fill=(255, 255, 255), font=font_badge)
        draw.text((230, y + 24), cmd, fill=TEXT_DARK, font=font_item_title)
        draw.text((115, y + 65), desc, fill=TEXT_MUTED, font=font_item_sub)
        y += 125

    # Right Card: Tray Features & Control
    _draw_card(draw, (1200, 180, 1860, 1020), "Tray-Funktionen & Aktionen", "Steuerung über das Benachrichtigungsfeld")

    bullets = [
        ("⚡ Sofort ausführen", "Startet die Warteschlangen-Abarbeitung auf Knopfdruck im Hintergrund-Thread."),
        ("➕ Aufgabe hinzufügen", "Unterstützt direkte Eingabe von rename-, move- und delete-Befehlen."),
        ("📁 Datenordner öffnen", "Direkter Zugriff auf queue.json, queue.txt und cloudlockfixer.log."),
        ("⏱ Intervall konfigurieren", "Wähle flexible Intervalle von 30 Minuten bis 12 Stunden."),
        ("🔄 Autostart & Kontextmenü", "Optionale Windows-Integration ohne Administratorrechte."),
        ("🛡 Sicherer Copy-Delete Fallback", "Vergleicht kryptografische Prüfsummen vor dem Entfernen."),
    ]

    y_b = 300
    for title, desc in bullets:
        draw.text((1230, y_b), title, fill=PRIMARY_COLOR, font=font_item_title)
        draw.text((1230, y_b + 28), desc, fill=TEXT_MUTED, font=font_item_sub)
        y_b += 110

    return canvas


def generate_frame_2(icon_img: Image.Image | None) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, canvas, "CloudLockFixer — Multi-Cloud-Provider-Erkennung", "Intelligente Erkennung nativer Sync-Pfade und Schutz virtueller Laufwerks-Mounts", icon_img)

    _draw_card(draw, (60, 180, 1860, 1020), "Unterstützte Cloud-Synchronisations-Clients", "Automatische Erkennung und dedizierte Sperr-Auflösung ohne Datenverlust")

    font_th = _get_font(18, bold=True)
    font_td = _get_font(16, bold=False)
    font_badge = _get_font(14, bold=True)

    # Table Header
    headers = [("Cloud-Provider", 100), ("Typ & Mount", 460), ("Prozess-Behandlung", 820), ("Status & Schutz", 1380)]
    for title, x in headers:
        draw.text((x, 290), title, fill=TEXT_DARK, font=font_th)
    draw.line([100, 330, 1820, 330], fill=CARD_BORDER, width=2)

    rows = [
        ("Microsoft OneDrive", "Folder Sync (%USERPROFILE%\\OneDrive)", "Taskkill mit automatischem Wiederanlauf", "Aktiv • Geschützt", SECONDARY_COLOR),
        ("Dropbox Desktop", "Folder Sync (%USERPROFILE%\\Dropbox)", "Graceful Pause/Resume via App-Binary", "Aktiv • Geschützt", SECONDARY_COLOR),
        ("Google Drive", "Virtual Mount (G:\\, Volume-Label Match)", "VIRTUAL MOUNT GUARD: Kein Kill/Pause!", "Mount geschützt", PRIMARY_COLOR),
        ("pCloud Drive", "Virtual Mount (P:\\, Volume-Label Match)", "VIRTUAL MOUNT GUARD: Kein Kill/Pause!", "Mount geschützt", PRIMARY_COLOR),
        ("Nextcloud / ownCloud", "Folder Sync (.config / Custom Root)", "Automatische Pfaderkennung aus Config", "Aktiv • Geschützt", SECONDARY_COLOR),
        ("Box Sync / Drive", "Folder Sync (%USERPROFILE%\\Box)", "Erkennung über Registry & Benutzerprofil", "Aktiv • Geschützt", SECONDARY_COLOR),
        ("Synology Drive Client", "Folder Sync (~\\SynologyDrive, custom configs)", "Fallback auf Daemon und UI-Binärdatei", "Aktiv • Geschützt", SECONDARY_COLOR),
    ]

    y_row = 360
    for prov, mount, proc, stat, color in rows:
        draw.text((100, y_row), prov, fill=TEXT_DARK, font=font_th)
        draw.text((460, y_row), mount, fill=TEXT_MUTED, font=font_td)
        draw.text((820, y_row), proc, fill=TEXT_MUTED, font=font_td)
        draw.rounded_rectangle([1380, y_row - 4, 1560, y_row + 28], radius=6, fill=color)
        draw.text((1395, y_row + 2), stat, fill=(255, 255, 255), font=font_badge)
        draw.line([100, y_row + 46, 1820, y_row + 46], fill=(241, 245, 249), width=1)
        y_row += 84

    return canvas


def generate_frame_3(icon_img: Image.Image | None) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, canvas, "CloudLockFixer — Präventiver Wächter & Einstellungen", "Proaktive Überwachung bei hoher Änderungsrate, konfigurierbare Retries und Benachrichtigungen", icon_img)

    # Left card: Preventive Watcher
    _draw_card(draw, (60, 180, 930, 1020), "Präventiver Wächter (PreventiveWatcher)", "Vermeidung von Sperren bei Massen-Dateiänderungen")

    font_t = _get_font(18, bold=True)
    font_d = _get_font(16, bold=False)

    left_points = [
        ("📈 Änderungsraten-Erkennung", "Registriert schnelle Dateisystem-Bursts (z. B. Entpacken oder Git-Checkouts) und pausiert den Sync-Client vorausschauend."),
        ("⏱ Intelligenter Cooldown-Timer", "Startet den Sync-Client erst dann wieder, wenn für eine konfigurierbare Ruhephase keine neuen Änderungen erfolgen."),
        ("🛡 Ausschluss virtueller Laufwerke", "Virtual-Mounts wie Google Drive oder pCloud werden niemals pausiert, um Verbindungsabbrüche zu verhindern."),
        ("📊 Detaillierte Statistiken", "Überwacht Änderungsereignisse pro Minute in Echtzeit im internen Log."),
    ]

    y_l = 310
    for title, desc in left_points:
        draw.text((90, y_l), title, fill=PRIMARY_COLOR, font=font_t)
        draw.text((90, y_l + 32), desc, fill=TEXT_MUTED, font=font_d)
        y_l += 140

    # Right card: Settings & Notifications
    _draw_card(draw, (990, 180, 1860, 1020), "Wiederholungen & Benachrichtigungen", "Vollständige Anpassbarkeit nach individuellen Anforderungen")

    right_points = [
        ("🔄 Flexible Retry-Limits", "Wähle zwischen Unbegrenzt (Default), 3, 5, 10 oder 20 Versuchen für vorübergehend gesperrte Dateien."),
        ("🔔 Windows System-Toasts", "Optionale Desktop-Benachrichtigungen bei dauerhaft fehlgeschlagenen oder blockierten Aufgaben."),
        ("🌐 Mehrsprachigkeit (i18n)", "Vollständige deutsche und englische Lokalisierung mit dynamischer Erkennung der Windows-Sprache."),
        ("🔒 Deterministischer Blockaden-Schutz", "Unlösbare Namens- und Pfadkonflikte werden transparent als 'blocked' markiert."),
    ]

    y_r = 310
    for title, desc in right_points:
        draw.text((1020, y_r), title, fill=SECONDARY_COLOR, font=font_t)
        draw.text((1020, y_r + 32), desc, fill=TEXT_MUTED, font=font_d)
        y_r += 140

    return canvas


def generate_frame_4(icon_img: Image.Image | None) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, canvas, "CloudLockFixer — Local-First & Zero-Egress Architektur", "100 % offline, datenschutzkonform und transparent ohne externe Server", icon_img)

    _draw_card(draw, (60, 180, 1860, 1020), "Sicherheits- & Architektur-Garantien", "Keine Netzwerk-Telemetrie • Keine Cloud-Übertragung • DSGVO-konform")

    font_t = _get_font(20, bold=True)
    font_d = _get_font(16, bold=False)

    cards = [
        ("🔒 Zero-Egress Prinzip", "CloudLockFixer öffnet keinerlei Netzwerkverbindungen nach außen. Es werden weder Nutzungsstatistiken noch Dateinamen oder Pfade übertragen.", (90, 310, 930, 480), PRIMARY_COLOR),
        ("📄 Offene Dateiformate", "Warteschlangen werden in lesbarem JSON (queue.json) und Klartext (queue.txt) geführt — ideal für Menschen, Shell-Skripte und lokale Tools.", (990, 310, 1830, 480), SECONDARY_COLOR),
        ("🛡 MSIX Desktop Bridge", "Standardisiertes Windows Store Paket (runFullTrust) mit sauberer Kapselung und verlässlicher Deinstallation ohne verbleibenden Datenmüll.", (90, 540, 930, 710), SECONDARY_COLOR),
        ("⚡ 100 % Lokale Ausführung", "Alle Konfigurationen und Protokolle verbleiben unter %LOCALAPPDATA%\\CloudLockFixer auf dem Gerät des Benutzers.", (990, 540, 1830, 710), PRIMARY_COLOR),
        ("⚖ Open Source unter MIT-Lizenz", "Freier, auditierbarer Quellcode auf GitHub mit umfassender Testabdeckung (285/285 automatisierte Tests).", (90, 770, 1830, 940), PRIMARY_COLOR),
    ]

    for title, desc, box, col in cards:
        draw.rounded_rectangle(box, radius=8, fill=(248, 250, 252), outline=CARD_BORDER, width=1)
        draw.text((box[0] + 30, box[1] + 25), title, fill=col, font=font_t)
        draw.text((box[0] + 30, box[1] + 65), desc, fill=TEXT_MUTED, font=font_d)

    return canvas


def generate_all_screenshots(project_root: Path | None = None) -> list[Path]:
    root = project_root or PROJECT_ROOT
    icon_path = root / "store_assets" / "icon_150x150.png"
    icon_img = None
    if icon_path.exists():
        try:
            icon_img = Image.open(icon_path).convert("RGBA")
        except Exception:
            icon_img = None

    frames = [
        ("01_tray-queue-management.png", generate_frame_1(icon_img)),
        ("02_multicloud-provider-support.png", generate_frame_2(icon_img)),
        ("03_preventive-watcher-settings.png", generate_frame_3(icon_img)),
        ("04_cross-platform-architecture.png", generate_frame_4(icon_img)),
    ]

    target_dirs = [
        root / "releases" / "windowsstore" / "screenshots",
        root / "screenshots" / "store",
        root / "README" / "screenshots" / "store",
    ]

    for d in target_dirs:
        d.mkdir(parents=True, exist_ok=True)

    output_files: list[Path] = []
    for filename, img in frames:
        primary_file = target_dirs[0] / filename
        img.save(primary_file, format="PNG", optimize=True)
        output_files.append(primary_file)

        for copy_dir in target_dirs[1:]:
            copy_file = copy_dir / filename
            shutil.copyfile(primary_file, copy_file)
            output_files.append(copy_file)

    return output_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Windows Store presentation screenshots for CloudLockFixer")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Project root directory")
    args = parser.parse_args()

    files = generate_all_screenshots(args.project_root)
    print(f"Successfully generated {len(files)} screenshot files across {len(set(f.parent for f in files))} directories.")
    for f in sorted(set(files)):
        print(f"  - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
