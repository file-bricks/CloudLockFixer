# Contributing to CloudLockFixer

Thank you for your interest in contributing to **CloudLockFixer** (`file-bricks/CloudLockFixer`), the resilient Windows tray and CLI tool for delayed, non-blocking rename, move, and delete operations inside cloud-synchronization folders.

[English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## English

### 1. Architectural Principles & Invariants

Every contribution must strictly preserve our 10 foundational system and operational invariants:

- **100% Local-First & Zero-Egress (`INV-LOCAL-01`)**: Zero unauthorized network sockets, telemetry, analytics beacons, or remote cloud connections. The engine operates completely air-gapped and offline.
- **Unprivileged Non-Elevation Execution (`INV-PRIV-02`)**: Executes strictly in user mode (`RunAsInvoker`), never requiring administrative privileges, root elevation, or UAC prompts.
- **Cryptographic Copy+Delete Fallback (`INV-SAFE-03`)**: Fallback copies verify bit-for-bit SHA-256 digests before the locked source file is unlinked; zero data loss guarantee.
- **Atomic Step Ordering (`INV-ATOM-04`)**: In multi-step operation chains (`1–4 steps`), Step $N$ executes strictly if Step $N-1$ succeeded. Destructive steps are skipped on upstream failure.
- **Configurable Retry Limits & Backoff (`INV-RETRY-05`)**: Configurable exponential retry backoff (base delay, multiplier, cap) and retry limits to resolve transient cloud-sync lock contention safely.
- **Desktop Notification Contract (`INV-NOTIF-06`)**: Emits non-intrusive desktop tray notifications on permanent failures or terminal conflicts without disrupting workflow.
- **Virtual Mount Guard (`INV-PROV-07`)**: Distinguishes between folder mounts (OneDrive, Dropbox) and virtual-drive mounts (Google Drive, pCloud); never pauses virtual mounts.
- **Multi-Host Conflict Defense (`INV-CONF-08`)**: Strict `.gitignore` blocking of cloud sync conflict copies (`*-conflict-*`, `* (Kopie)*`) and multi-agent coordination locks (`LOCK.*`).
- **Deterministic CI Guardrails (`INV-CI-09`)**: Multi-OS test matrix with deterministic timeout bounds (`15m` / `10m` / `5m`), compileall bytecode verification, and concurrency cancel-in-progress.
- **Bilingual Security SLA & Compliance (`INV-SLA-10`)**: Immutable Level 1 SBOM transparency, statutory disclaimer under § 521 BGB, and a binding 48h Security Response SLA.

### 2. Local Development & Setup

1. **Clone the repository** (Plan D canonical local clone):
   ```bash
   git clone https://github.com/file-bricks/CloudLockFixer.git
   cd CloudLockFixer
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

### 3. Testing & Verification Gates

Before submitting any Pull Request or pushing changes, verify that all four quality gates pass cleanly:

1. **Run full automated test suite**:
   ```bash
   pytest
   ```
   All contract, unit, and metadata tests must pass (100% green).
2. **Run Ruff static analysis**:
   ```bash
   ruff check .
   ```
3. **Verify Python compilation**:
   ```bash
   python -m compileall -q src tests
   ```
4. **Verify git diff cleanliness**:
   ```bash
   git diff --check
   ```

### 4. Version Freeze & Release Discipline

- **Version Freeze (`T-20260920-167562623`)**: Do not bump or increment the package version in `pyproject.toml`, source code, or manifests. Version bumps are strictly governed by coordinated release procedures. All additions must be documented under `## [Unreleased]` in `CHANGELOG.md`.
- **Conventional Commits**: Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).

### 5. Reporting Security Vulnerabilities

Please do not open public GitHub issues for security vulnerabilities. Instead, refer to our [Security Policy](SECURITY.md) and report via `security@open-bricks.org` or `security@file-bricks.org` in accordance with our binding 48-hour response SLA.

### 6. Statutory Disclaimer (§ 521 BGB)

This software is provided free of charge under the MIT License as open-source software. In accordance with § 521 of the German Civil Code (BGB - Schenkungs- und Gefälligkeitsrecht), liability for defects in quality and title is strictly limited to intent and gross negligence.

---

<a id="deutsch"></a>
## Deutsch

### 1. Architektonische Prinzipien & Invarianten

Jeder Beitrag muss unsere 10 grundlegenden System- und Betriebsinvarianten wahren:

- **100% Local-First & Zero-Egress (`INV-LOCAL-01`)**: Keine unerlaubten ausgehenden Netzwerk-Sockets, Telemetrie, Analyse-Beacons oder Cloud-Verbindungen. Die Engine arbeitet vollständig offline.
- **Nicht-privilegierte Ausführung (`INV-PRIV-02`)**: Strikter Benutzermodus (`RunAsInvoker`), niemals Administrator- oder Root-Rechte oder UAC-Prompts erforderlich.
- **Kryptographisches Copy+Delete-Fallback (`INV-SAFE-03`)**: Fallback-Kopien verifizieren vor dem Löschen der gesperrten Quelldatei bitgenaue SHA-256-Prüfsummen; Garantie gegen Datenverlust.
- **Atomare Schritt-Reihenfolge (`INV-ATOM-04`)**: In mehrschrittigen Operationsketten (1–4 Schritte) wird Schritt $N$ nur ausgeführt, wenn Schritt $N-1$ erfolgreich war. Destruktive Schritte stoppen bei Fehlern sofort.
- **Konfigurierbare Wiederholungslimits & Backoff (`INV-RETRY-05`)**: Konfigurierbarer exponentieller Backoff (Basis, Multiplikator, Deckel) und Retry-Limits zur sicheren Auflösung von Synchronisationssperren.
- **Desktop-Benachrichtigungsvertrag (`INV-NOTIF-06`)**: Sendet dezente System-Tray-Benachrichtigungen bei dauerhaften Fehlern oder Konflikten ohne Arbeitsunterbrechung.
- **Virtueller Mount-Wächter (`INV-PROV-07`)**: Unterscheidet zwischen Ordner-Mounts (OneDrive, Dropbox) und virtuellen Laufwerken (Google Drive, pCloud); pausiert virtuelle Mounts niemals.
- **Multi-Host-Konfliktabwehr (`INV-CONF-08`)**: Strikte `.gitignore`-Blockierung von Cloud-Sync-Konfliktdateien (`*-conflict-*`, `* (Kopie)*`) und Multi-Agenten-Sperren (`LOCK.*`).
- **Deterministische CI-Leitplanken (`INV-CI-09`)**: Multi-OS-Testmatrix mit deterministischen Timeouts (`15m` / `10m` / `5m`), Bytecode-Kompilierung (`compileall`) und Concurrency Cancel-in-Progress.
- **Bilinguale Sicherheits-SLA & Compliance (`INV-SLA-10`)**: Vollständige Level 1 SBOM-Transparenz, gesetzlicher Haftungsausschluss gem. § 521 BGB und verbindliche 48h Security Response SLA.

### 2. Lokale Entwicklung & Einrichtung

1. **Repository klonen** (Kanonischer lokaler Klon gem. Plan D):
   ```bash
   git clone https://github.com/file-bricks/CloudLockFixer.git
   cd CloudLockFixer
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

### 3. Test- & Verifikations-Gates

Vor jedem Pull Request oder Push müssen alle vier Qualitätsprüfungen fehlerfrei bestehen:

1. **Vollständige Testsuite ausführen**:
   ```bash
   pytest
   ```
   Alle Contract-, Unit- und Metadaten-Tests müssen zu 100% grün sein.
2. **Ruff statische Analyse**:
   ```bash
   ruff check .
   ```
3. **Python-Bytecode-Kompilierung prüfen**:
   ```bash
   python -m compileall -q src tests
   ```
4. **Git-Diff-Sauberkeit prüfen**:
   ```bash
   git diff --check
   ```

### 4. Versions-Freeze & Release-Disziplin

- **Versions-Freeze (`T-20260920-167562623`)**: Erhöhen Sie die Versionsnummer in `pyproject.toml`, Quellcode oder Manifesten nicht eigenmächtig. Versionsanhebungen unterliegen koordinierten Release-Prozeduren. Alle Änderungen werden unter `## [Unreleased]` in `CHANGELOG.md` erfasst.
- **Conventional Commits**: Nutzen Sie standardisierte Commit-Präfixe (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).

### 5. Melden von Sicherheitslücken

Bitte öffnen Sie keine öffentlichen GitHub Issues für Sicherheitslücken. Wenden Sie sich gemäß unserer [Sicherheitsrichtlinie](SECURITY.md) an `security@open-bricks.org` oder `security@file-bricks.org` für eine Rückmeldung innerhalb unserer verbindlichen 48-Stunden-SLA.

### 6. Gesetzlicher Haftungsausschluss (§ 521 BGB)

Diese Software wird unentgeltlich unter der MIT-Lizenz als Open-Source-Software bereitgestellt. Gemäß § 521 BGB (Schenkungs- und Gefälligkeitsrecht) ist die Haftung für Sach- und Rechtsmängel auf Vorsatz und grobe Fahrlässigkeit beschränkt.
