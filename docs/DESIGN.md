# CloudLockFixer (CLF-WDAS) — Design / Spec

**Stand:** 2026-05-29 · **Status:** freigegeben (Brainstorming abgeschlossen)
**Kürzel:** CLF-WDAS = CloudLockFixer *with Delayed Action Service*
**GUI:** PySide6 · **Plattform:** Windows

## Problem

Der Windows-**Cloud-Files-Filtertreiber `cldflt.sys`** (installiert von OneDrive, Dropbox, Google Drive, iCloud — allen, die die Cloud Files API nutzen) fängt `rename()` auf Treiber-Ebene ab und gibt „Zugriff verweigert"/EXDEV zurück, solange er aktiv ist. Zusätzlich halten der **Windows-Such-Indexer** + der Sync-Client Handles auf frisch geänderte Dateien. Folge: Ordner/Dateien in Cloud-Sync-Ordnern lassen sich oft nicht in-place umbenennen/verschieben.

**Belegt (MS-empfohlener Workaround):** `rename()` durch **copy()+delete()** ersetzen — funktioniert unabhängig vom Filter. (Empirisch bestätigt: cross-volume Move klappt.)

## Ziel

Ein Tray-Tool, in das man Ordner-/Datei-Operationen **einträgt** und das sie **fire & forget** zuverlässig erledigt — sofort wenn möglich, sonst verzögert per Retry, providerübergreifend.

## Use-Cases (Ketten, 1–4 Glieder)

1. **Live-Edit-Übernahme:** Original-Ordner löschen → danach den lokal geänderten Ordner an den Ursprungsort verschieben. (delete → move, „delete erst nach Erfolg des move").
2. **Verzögert umbenennen:** Ordner/Datei umbenennen, sobald in einem Lauf möglich.
3. **Verzögert verschieben.**
(+ Löschen als eigenständige Aktion.)

## Architektur (All-in-one PySide6-Tray-Prozess)

**1. Core (provider-agnostisch, headless testbar)**
- **Queue-Store:** `queue.json` (Programm) + `queue.txt` (Mensch/LLM tippt Zeilen, einfache Syntax) → werden gemerged.
- **Task = Kette aus 1–4 Schritten.** Schritt-Typen: `rename`, `move`, `delete`, `copy`. Status: pending→running→done/failed; retry_count; created/last_try.
- **Sichere Ausführung:** Schritt N nur nach Erfolg N-1. Destruktive Schritte (delete) **erst nach** erfolgreichem Voraus-Schritt; Vorbedingungen prüfen (Ziel existiert/nicht leer) → kein Datenverlust.
- **Universelle Primitive = copy+delete** (`ops.py`): rename/move werden als copy→verify→delete umgesetzt (umgeht `cldflt`). Reiner in-place-Versuch zuerst (schnell), bei „Zugriff verweigert"/EXDEV automatisch copy+delete-Fallback.
- **Worker:** bei Start + periodisch (Default **2 h**, einstellbar in 30-min-Schritten) + „Jetzt". Offene Tasks werden jeden Lauf neu versucht; erledigte → DONE/Log.

**2. Provider-Adapter (`providers.py`, dünn, pluggbar)**
- Interface `SyncProvider`: `is_running()`, `pause()` (beenden), `resume()` (neu starten), `owns_path(p)`.
- **OneDriveProvider** jetzt implementiert (kill `OneDrive.exe` / start `OneDrive.exe /background`).
- Dropbox/GoogleDrive/iCloud-Adapter vorgesehen, aber **YAGNI** (erst bei Bedarf). Core funktioniert auch ohne Pause rein über copy+delete.

**3. Tray (`tray.py`, PySide6 QSystemTrayIcon)**
- Icon OneDrive-ähnlich in **Grün**. Menü: „n offen", „Jetzt ausführen", „Task hinzufügen…" (Dialog: Quelle + Aktion + Ziel/Name), Queue/Log anzeigen, Intervall (30-min-Schritte), Beenden.
- **Autostart** via HKCU `…\Run`-Key.
- Single-Instance-Guard.

**4. Eingabe-Wege**
- **CLI** (`cli.py`, für LLM/Skripte): `clf add --rename <src> <neu>` · `--move <src> <ziel>` · `--delete <pfad>` · `--chain "<schritt>;<schritt>;…"` · `list` · `run-now`.
- **`queue.txt`** (Mensch/LLM): eine Zeile pro Task.
- **Explorer-Rechtsklick** „CLF: verzögert umbenennen/verschieben/löschen" (Shell-Kontextmenü → ruft CLI) — **P2**.
- **Tray-Dialog** (GUI).

**5. Präventiv-Wächter (`watcher.py`) — P3, optional**
- Beobachtet Änderungsrate in Cloud-Ordnern; bei viel Aktivität → Sync-Client automatisch pausieren; nach Cooldown ohne Änderungen → wieder starten. Fängt Locks präventiv ab.

## Fehlerbehandlung
- Pro Task `max_retries` (Default unbegrenzt für „irgendwann", aber Backoff); Dauerfehler → `failed` + Tray-Badge.
- Nichts Destruktives ohne erfüllte Vorbedingung. Jede Aktion geloggt (`clf.log`).

## Tests
- `pytest`: Queue-Parsing (json+txt), Ketten-Reihenfolge/Abbruch, `ops` copy+delete + rename/move-Fallback auf Temp-Ordnern, „delete erst nach Erfolg", Provider-Pause gemockt. Tray manuell.

## Phasen
- **P1 (MVP):** Core + `ops` (copy+delete) + OneDriveProvider + Worker + CLI + Tray + Autostart + Tests.
- **P2:** Explorer-Kontextmenü.
- **P3:** Präventiv-Wächter; weitere Provider-Adapter bei Bedarf.

## Datenfluss (kurz)
`CLI/queue.txt/Tray` → Task in `queue.json` → Worker (Start/Timer/Jetzt) → pro Task: (optional Provider.pause) → Kette Schritt-für-Schritt via `ops` (in-place try → copy+delete-Fallback) → Erfolg: done/Log; Fehler: retry später → (Provider.resume).
