# Exportformat für CloudLockFixer

**Stand:** 2026-10-30  
**Schema:** `cloudlockfixer-snapshot-v1`  
**Spezifikation:** Version 1.0.0  

---

## 1. Grundsatz & Sicherheitsprinzipien (Zero-Secrets & Local-First)

CloudLockFixer verwaltet Datei- und Ordneroperationen, die durch Cloud-Synchronisationsdienste temporär blockiert sind. Um den aktuellen Queue-Status, Backoff-Fristen, Sync-Provider und Einstellungen geräteübergreifend und mobil einsehen zu können, definiert dieses Dokument das offizielle, schreibgeschützte Snapshot-Format.

1. **Local-First & Read-Only:** Der Snapshot dient ausschließlich der Statusüberprüfung, Diagnose und mobilen Anzeige im Web-Companion. Er transportiert keine ausführenden Payloads und eröffnet keine Remote-Steuerung.
2. **Zero-Secrets & Datenschutz:** Es werden niemals Zugangsdaten, OAuth-Tokens, Passwörter oder private Cloud-Schlüssel exportiert. Dateipfade werden strukturiert bereitgestellt und für sensible Anzeigen auf Basenamen und relative Indikatoren beschränkt.
3. **Deterministisches JSON:** Vollständig UTF-8-kodiertes JSON mit standardisierten ISO-8601-Zeitstempeln in UTC (`Z`).
4. **Atomare Erstellung:** Exporte erfolgen atomar via temporäre Staging-Dateien (`.tmp`) und `os.replace` mit Berechtigungs- und Retry-Resilienz.

---

## 2. Dateiformat: `cloudlockfixer-snapshot-v1.json`

### Kanonischer Aufbau

```json
{
  "$schema": "https://schemas.file-bricks.org/cloudlockfixer/snapshot-v1.json",
  "schema_name": "cloudlockfixer-snapshot-v1",
  "schema_version": "1.0.0",
  "generated_at": "2026-10-30T09:20:00Z",
  "app": {
    "name": "CloudLockFixer",
    "version": "0.2.3",
    "license": "MIT",
    "homepage": "https://github.com/file-bricks/CloudLockFixer"
  },
  "environment": {
    "platform": "win32",
    "python_version": "3.12.10",
    "data_dir_name": "CloudLockFixer"
  },
  "settings": {
    "interval_min": 120,
    "max_retries": null,
    "notifications_enabled": true,
    "language": "de",
    "backoff_base_sec": 60,
    "backoff_max_sec": 3600,
    "backoff_multiplier": 2.0
  },
  "queue_summary": {
    "total": 3,
    "pending": 2,
    "in_progress": 0,
    "deferred": 1,
    "failed": 1,
    "permanent_failed": 0,
    "done": 0
  },
  "tasks": [
    {
      "id": "e2f1a8c4",
      "status": "pending",
      "retry_count": 2,
      "created_at": "2026-10-30T08:00:00Z",
      "last_try": "2026-10-30T08:15:00Z",
      "last_error": "WinError 32: Prozess greift auf Datei zu",
      "last_outcome": "retryable",
      "step_index": 0,
      "next_try_at": "2026-10-30T08:35:00Z",
      "is_due": false,
      "steps": [
        {
          "op": "rename",
          "src_name": "AltDokument.docx",
          "src_display": "C:/Users/.../OneDrive/Dokumente/AltDokument.docx",
          "arg_display": "NeuDokument.docx"
        }
      ]
    }
  ],
  "providers": [
    {
      "name": "OneDrive",
      "mount_type": "folder",
      "is_running": true,
      "roots_count": 1
    },
    {
      "name": "Google Drive",
      "mount_type": "virtual",
      "is_running": false,
      "roots_count": 1
    }
  ]
}
```

---

## 3. Feldspezifikation

### Root-Ebene
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `$schema` | String | URL zum JSON-Schema für Validierungswerkzeuge |
| `schema_name` | String | Festwert `"cloudlockfixer-snapshot-v1"` |
| `schema_version` | String | SemVer des Schemas (z. B. `"1.0.0"`) |
| `generated_at` | String | ISO-8601 Zeitstempel der Erstellung in UTC |
| `app` | Object | Anwendungsname, Version, Lizenz und Homepage |
| `environment` | Object | Betriebssystem, Python-Laufzeit und Datenverzeichnisname |
| `settings` | Object | Relevante Konfigurationsparameter (Intervall, Limits, Backoff) |
| `queue_summary` | Object | Aggregierte Zähler aller Aufgaben nach Status |
| `tasks` | Array | Liste der Aufgaben mit Einzelschritten und Retry-Zustand |
| `providers` | Array | Liste der erkannten Synchronisationsdienste und deren Status |

### Task-Ebene
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | String | Eindeutige Task-ID (z. B. 8 Hex-Zeichen) |
| `status` | String | `pending`, `running`, `done`, `failed`, `permanent_failed` |
| `retry_count` | Integer | Bisherige Anzahl von Wiederholungsversuchen |
| `created_at` | String | Erstellungszeitpunkt |
| `last_try` | String | Zeitpunkt des letzten Ausführungsversuchs |
| `last_error` | String | Letzter Fehlerbeleg (z. B. WinError 32 oder EBUSY) |
| `last_outcome` | String | Klassifikation: `retryable`, `permanent`, etc. |
| `step_index` | Integer | Aktueller Schrittzeiger in der Aktionskette |
| `next_try_at` | String | Geplanter nächster Retry-Zeitpunkt bei exponentiellem Backoff |
| `is_due` | Boolean | `true`, falls der Backoff abgelaufen ist oder kein Backoff vorliegt |
| `steps` | Array | Kette von Dateioperationen (`rename`, `move`, `delete`) |

---

## 4. Nutzung im Web-Companion

Der Web-Companion (`web_companion/index.html`) konsumiert diese Datei direkt über den Browser-File-Picker oder Drag & Drop. Das Parsing erfolgt zu 100% lokal im Client via JavaScript (`JSON.parse`). Es werden keine Daten an externe Server übertragen (Zero-Egress).
