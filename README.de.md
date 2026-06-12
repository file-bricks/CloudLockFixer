# CloudLockFixer (CLF-WDAS)

> 🇬🇧 **English version:** [README.md](README.md)

**CloudLockFixer** *with Delayed Action Service* — ein Windows-Tray-Tool, das
Datei-/Ordner-Operationen (**umbenennen / verschieben / löschen**) in Cloud-Sync-
Ordnern zuverlässig erledigt, auch wenn sie der Windows-Cloud-Files-Filter
(`cldflt`) gerade blockiert. Man **trägt eine Aktion ein** und sie wird
**„irgendwann" automatisch** ausgeführt — fire & forget.

## Warum?

`cldflt.sys` (von OneDrive, Dropbox, Google Drive, iCloud installiert) fängt
`rename()` ab und liefert „Zugriff verweigert"/EXDEV, solange er aktiv ist.
**MS-empfohlener Workaround:** `rename()` durch **copy()+delete()** ersetzen —
genau das macht dieses Tool, plus verzögerte Retries und optionales Pausieren
des Sync-Clients.

## Einstieg

| Bedarf | Einstieg |
|---|---|
| OneDrive- oder Cloud-Files-Fehler „Zugriff verweigert" beim Umbenennen/Verschieben/Löschen beheben | Tray-App mit `START.bat` starten und verzögerte Aufgabe hinzufügen |
| Blockierte Dateioperationen aus Skripten oder LLM-Agenten automatisieren | `PYTHONPATH=src python -m cloudlockfixer.cli` nutzen |
| Sicherheitsmodell vor destruktiven Aktionen prüfen | [`docs/DESIGN.md`](docs/DESIGN.md) lesen |
| Aufgaben ohne UI eintragen | `%LOCALAPPDATA%\CloudLockFixer\queue.txt` bearbeiten |
| Quellbaum verifizieren | `PYTHONPATH=src python -m pytest -q` ausführen |

## Funktionen

- Datei-/Ordner-Operationen eintragen und fire & forget ausführen lassen
- `copy+delete`-Fallback, der die `cldflt`-Sperre automatisch umgeht
- Ketten aus 1–4 Schritten mit sicherer Reihenfolge — destruktive Schritte
  laufen erst nach Erfolg des Voraus-Schritts (kein Datenverlust)
- Mehrere Eingabewege: **CLI** (für LLM/Skripte), menschenlesbare **`queue.txt`**,
  **Tray-Dialog** und **Explorer-Rechtsklick**-Kontextmenü
- Auto-Retry in einstellbarem Intervall (Default 2 h) und auf Abruf
- Optionales Pausieren/Neustarten des Sync-Clients während einer Operation
  (OneDrive-Provider)
- Optionaler Präventiv-Wächter, der den Sync-Client je nach Ordner-Aktivität
  pausiert/fortsetzt
- Autostart mit Windows; Single-Instance-Tray-App

## Installation

### Voraussetzungen
- Windows (der `cldflt`-Filter ist Windows-spezifisch)
- Python 3.10+
- PySide6 (>= 6.7)

### Schritte
1. Repository klonen
2. `pip install -r requirements.txt`
3. Tray-App starten: Doppelklick `START.bat` oder
   `PYTHONPATH=src python -m cloudlockfixer`

## Nutzung

### Tray-App
Startet mit Windows, wenn Autostart aktiviert ist. Tray-Menü: *Task hinzufügen…*,
*Jetzt ausführen* (auch *mit OneDrive-Pause*), *Intervall* (30-min-Schritte,
Default 2 h), *Mit Windows starten*, *Queue/Log öffnen*.

### CLI (für LLM/Skripte)
```
clf add --rename "C:\...\AltOrdner" "NeuName"
clf add --move   "C:\local\x"        "C:\onedrive\x"
clf add --delete "C:\onedrive\alt"
clf add --chain  'move "C:\local\x" "C:\onedrive\x" && delete "C:\onedrive\alt"'
clf list
clf run-now [--pause]
```
(Aufruf in dev: `PYTHONPATH=src python -m cloudlockfixer.cli ...`)

### queue.txt (Mensch/LLM)
Datei in `%LOCALAPPDATA%\CloudLockFixer\queue.txt`, eine Zeile pro Task
(`rename` / `move` / `delete`, Verkettung mit `&&`). Aufgenommene Zeilen werden
automatisch zu `#>` auskommentiert.

## Funktionsweise

- **Ketten (1–4 Glieder):** Schritt N läuft nur nach Erfolg von N-1.
  Destruktives (`delete`) erst nach erfolgreichem Voraus-Schritt → kein
  Datenverlust.
- **copy+delete als Primitive:** in-place wird zuerst versucht, bei Sperre
  automatisch copy → verify → delete. Idempotent (Retry sicher).
- **Worker:** bei Start + alle 2 h (einstellbar) + manuell. Hängt ein Task
  mehrfach, wird der zuständige Sync-Client für den Lauf pausiert und danach
  neu gestartet.

## Auffindbarkeit

Nützliche Suchphrasen: `OneDrive Zugriff verweigert umbenennen`,
`cldflt.sys Datei gesperrt`, `Windows Cloud Files Filter copy delete fallback`,
`OneDrive 0x8007016A Dateioperation`, `Dropbox Google Drive iCloud gesperrter
Ordner Retry` und `CloudLockFixer queue.txt`.

CloudLockFixer ist kein generischer File-Unlocker, kein Anti-Malware-Werkzeug,
kein Backup-Client und kein Ersatz für Cloud-Speicher. Es ist eine lokale
Queue- und Retry-Hilfe für Dateien, die bereits unter Kontrolle des Nutzers
stehen, aber temporär durch einen Cloud-Sync-Provider blockiert werden.

## Status / Roadmap

- **P1 (fertig):** Core (copy+delete, Ketten, Retry) · CLI · `queue.txt` · Tray ·
  Autostart · OneDrive-Provider.
- **P2 (fertig):** Explorer-Rechtsklick-Kontextmenü (HKCU-Kaskade, opt-in via
  Tray-Toggle).
- **P3 (fertig):** Präventiv-Wächter (Änderungsrate *konfigurierter* Ordner
  beobachten → Sync-Client automatisch pausieren/fortsetzen; bounded + stat-only,
  hydratisiert keine Online-only-Placeholder; opt-in).
- **Tests:** `pytest`, **88 grün** (Core + P2/P3 + i18n + Multicloud-Regressionen).
- **Im Lifetest gehärtet (2026-05-29):** `is_running()/pause()` robust gegen
  nicht-UTF-8-`tasklist`-Ausgabe; `delete` entfernt read-only-Attribute statt an
  WinError 5 zu scheitern. Erster echter Einsatz: ein Ordner-Rename, den manuelle
  Versuche/`cldflt` zuvor blockierten, gelang per copy+delete.
- **Offen/künftig:** weitere Provider-Adapter (Dropbox/Google Drive/iCloud);
  optional Relaunch-Unterdrückung des Sync-Clients während langer Operationen.

Windows-only (`cldflt` ist Windows-spezifisch); der Kern ist plattformneutral
für spätere Ports. Design: [`docs/DESIGN.md`](docs/DESIGN.md).

## Lizenz

MIT — siehe [LICENSE](LICENSE).

Dieses Projekt nutzt **PySide6** (Qt for Python) unter der **LGPL v3**. PySide6
wird als unveränderte Drittanbieter-Abhängigkeit verwendet.
