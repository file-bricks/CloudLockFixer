# CloudLockFixer (CLF-WDAS) — Design / Spec

**Stand:** 2026-08-11 · **Status:** Source-/CI-Vertrag (kein nativer Release- oder Security-Freigabestatus)
**Prüfbasis:** Arbeitskopie `b1aa1c6` plus vorhandene lokale Änderungen; der Klon ist nicht clean.
**Kürzel:** CLF-WDAS = CloudLockFixer *with Delayed Action Service*
**GUI:** PySide6 · **Plattform:** Windows (Hauptziel; Linux/macOS via Source & CI-Smoke)

## Problem

Der Windows-**Cloud-Files-Filtertreiber `cldflt.sys`** (installiert von OneDrive, Dropbox, Google Drive, iCloud — allen, die die Cloud Files API nutzen) fängt `rename()` auf Treiber-Ebene ab und gibt „Zugriff verweigert"/EXDEV zurück, solange er aktiv ist. Zusätzlich halten der **Windows-Such-Indexer** + der Sync-Client Handles auf frisch geänderte Dateien. Folge: Ordner/Dateien in Cloud-Sync-Ordnern lassen sich oft nicht in-place umbenennen/verschieben.

**Belegt (MS-empfohlener Workaround):** `rename()` durch **copy()+delete()** ersetzen — funktioniert unabhängig vom Filter. (Empirisch bestätigt: cross-volume Move klappt. `ops._payload_signature()` sichert die Kopie vor dem Löschen per SHA-256-Inhaltsdigest ab.)

## Ziel

Ein Tray-Tool, in das man Ordner-/Datei-Operationen **einträgt** und das sie **fire & forget** zuverlässig erledigt — sofort wenn möglich, sonst verzögert per Retry, providerübergreifend.

## Use-Cases (Ketten)

1. **Live-Edit-Übernahme:** Original-Ordner löschen → danach den lokal geänderten Ordner an den Ursprungsort verschieben. (delete → move, „delete erst nach Erfolg des move").
2. **Verzögert umbenennen:** Ordner/Datei umbenennen, sobald in einem Lauf möglich.
3. **Verzögert verschieben.**
(+ Löschen als eigenständige Aktion; der aktuelle Parser unterstützt `rename`, `move` und `delete`.)

## Architektur (All-in-one PySide6-Tray-Prozess)

**1. Core (provider-agnostisch, headless testbar)**
- **Queue-Store:** `queue.json` (Programm) + `queue.txt` (Mensch/LLM tippt Zeilen, einfache Syntax) → werden gemerged.
- **Task = Kette aus mindestens einem Schritt.** `queue.txt` und CLI trennen Schritte mit `&&`; der aktuelle Parser akzeptiert `rename`, `move` und `delete`. Status: pending→running→done/blocked/failed; `last_outcome` hält `done`, `retryable`, `blocked` oder `permanent`; dazu retry_count, created/last_try.
- **Sichere Ausführung:** Schritt N folgt erst auf den Erfolg von N-1. Bei `move`/`rename` wird die copy+delete-Fallback-Kopie vor dem Quell-Löschen per SHA-256-Inhaltsdigest verifiziert; ein Fehlschlag bleibt für einen späteren Versuch offen.
- **Universelle Primitive = copy+delete** (`ops.py`): rename/move werden als copy→verify→delete umgesetzt (umgeht `cldflt`). Reiner in-place-Versuch zuerst (schnell), bei „Zugriff verweigert"/EXDEV automatisch copy+delete-Fallback.
- **Worker:** bei Start + periodisch (Default **2 h**, einstellbar in 30-min-Schritten) + „Jetzt". Retryfähige Tasks bleiben standardmäßig bis zum Erfolg `pending`; nur ein expliziter endlicher `max_retries`-Aufruf setzt nach dem Limit dauerhaft `failed`.

**2. Provider-Adapter (`providers.py`, dynamische Auto-Discovery)**
- Interface `SyncProvider`: `is_running()`, `pause()` (beenden), `resume()` (neu starten), `owns_path(p)`, `mount_type` ("folder"/"virtual").
- **Unterstützte Provider (8 Clients):** OneDrive, Google Drive, Dropbox, iCloud, Box, Nextcloud, pCloud, Synology Drive.
- Virtuelle Mounts (z. B. Google Drive, pCloud) schalten `pause()`-Aktionen automatisch ab, um Dateisystem-Unmounts zu verhindern.

**3. Tray (`tray.py`, PySide6 QSystemTrayIcon)**
- Icon OneDrive-ähnlich in **Grün**. Menü: Status „n offen", „Jetzt ausführen", „Task hinzufügen…" (Dialog: Quelle + Aktion + Ziel/Name), **Datenordner öffnen** (`queue.txt` und Logs), Intervall (30-min-Schritte), Beenden. Ein separater Queue-/Log-Viewer ist nicht Bestandteil des aktuellen Menüs.
- **Autostart:** Windows-Registry (`HKCU\...\Run`), Linux-XDG-Autostart (`.config/autostart`), macOS LaunchAgent (`~/Library/LaunchAgents`).
- Single-Instance-Guard.

**4. Eingabe-Wege**
- **CLI** (`cli.py`, für LLM/Skripte): `clf add --rename <src> <neu>` · `--move <src> <ziel>` · `--delete <pfad>` · `--chain "<schritt> && <schritt> && …"` · `list` · `run-now`.
- **`queue.txt`** (Mensch/LLM): eine Zeile pro Task.
- **Explorer-Rechtsklick** „CLF: verzögert umbenennen/verschieben/löschen" (Shell-Kontextmenü → ruft CLI) — **P2**.
- **Tray-Dialog** (GUI).

**5. Präventiv-Wächter (`watcher.py`) — P3, optional**
- Beobachtet Änderungsrate in Cloud-Ordnern; bei viel Aktivität → Sync-Client automatisch pausieren; nach Cooldown ohne Änderungen → wieder starten. Fängt Locks präventiv ab.

## Fehlerbehandlung
- `max_retries` ist standardmäßig `None`: retryfähige Tasks bleiben pending und werden weiter aufgegriffen. Ein Aufrufer kann ein endliches Limit setzen; ein persistierbares Backoff-/Retry-Profil bleibt offen.
- Deterministische Ziel- oder Eingabekonflikte werden als `blocked` persistiert und nicht endlos erneut versucht. Ein explizites Retry-Limit markiert weiterhin `permanent`/`failed`.
- Nichts Destruktives ohne erfüllte Vorbedingung. Jede Aktion geloggt (`clf.log`).

## Tests
- `PYTHONPATH=src python -m pytest -q`: aktuell **167 Tests gesammelt** (lokaler Source-/CI-Vertrag; native GUI-/Provider-Live-Smokes bleiben offen). Abgedeckt sind Queue-Parsing (JSON+TXT), Ketten-Reihenfolge/Abbruch, copy+delete-Verify, unbegrenzter Retry-Default plus optionales Limit, persistierte Blockierung bei Zielkonflikten, Provider-/Virtual-Mount-Guards, Autostart-Verträge und Cross-Platform-Pfade.

## Phasen
- **P1 (MVP):** Core + `ops` (copy+delete) + OneDriveProvider + Worker + CLI + Tray + Autostart + Tests.
- **P2:** Explorer-Kontextmenü.
- **P3:** Präventiv-Wächter; weitere Provider-Adapter bleiben optionaler Ausbau.

## Datenfluss (kurz)
`CLI/queue.txt/Tray` → Task in `queue.json` → Worker (Start/Timer/Jetzt) → pro Task: (optional Provider.pause, nicht bei Virtual Mounts) → Kette Schritt-für-Schritt via `ops` (in-place try → copy+delete-Fallback mit Verify) → Erfolg: done/Log; retryfähiger Fehler: pending für späteren Lauf; deterministischer Zielkonflikt: blocked; explizites Limit erreicht: permanent/failed → (Provider.resume).
