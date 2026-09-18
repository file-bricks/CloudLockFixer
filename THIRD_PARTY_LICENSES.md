# Third-Party Licenses & Software Inventory — Software Bill of Materials (SBOM)

**Project:** `CloudLockFixer` (CLF-WDAS: Windows Tray & CLI Delayed Action Service for Cloud-Sync Folders)  
**License:** [MIT License](LICENSE)  
**Audit Date:** 2026-09-18  
**Repository:** [file-bricks/CloudLockFixer](https://github.com/file-bricks/CloudLockFixer)  
**Organization:** [file-bricks](https://github.com/file-bricks)  
**Umbrella Collective:** [open-bricks](https://github.com/open-bricks)  

---

## Runtime Architecture & Dependencies

`CloudLockFixer` is a resilient Windows system tray and CLI tool built with **Python 3** and **PySide6 (Qt 6)** that resolves file operation locks (`cldflt.sys` / `WinError 5` / `EXDEV`) inside cloud synchronization roots (OneDrive, Dropbox, Google Drive, Box, iCloud, Nextcloud, pCloud, and Synology Drive). It guarantees unprivileged local-first execution, cryptographic SHA-256 copy+delete data integrity, deterministic multi-step operation chaining, and zero external runtime telemetry or network egress.

### Runtime Dependencies

| Package / Library | Version Constraint | License | SPDX Identifier | Upstream URL | Purpose |
|---|---|---|---|---|---|
| **PySide6** | `>=6.7.0` | LGPL-3.0-only | `LGPL-3.0-only` | [PySide6 on PyPI](https://pypi.org/project/PySide6/) | Official Python Qt6 bindings for GUI, system tray, task dialog, and desktop event integration. |
| **shiboken6** | `>=6.7.0` | LGPL-3.0-only | `LGPL-3.0-only` | [shiboken6 on PyPI](https://pypi.org/project/shiboken6/) | CPython binding generator runtime companion library powering PySide6. |
| **Python Standard Library** | `>=3.10` | Python Software Foundation License 2.0 | `PSF-2.0` | [Python PSF](https://docs.python.org/3/license.html) | Native standard library (`os`, `shutil`, `hashlib`, `pathlib`, `json`, `winreg`, `ctypes`). |

Zero runtime npm packages, external tracking scripts, or cloud analytics brokers are embedded into the desktop application or CLI runtime.

---

### Development, Tooling & Packaging Dependencies

The following tools are utilized strictly for local development, code quality enforcement, static analysis, packaging, and CI automation:

| Tool / Framework | Version Floor | License | SPDX Identifier | Project / Organization | Purpose |
|---|---|---|---|---|---|
| **pytest** | `>=9.1.1` | MIT | `MIT` | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Automated Python contract, regression, and unit testing framework. |
| **pluggy** | `>=1.0.0` | MIT | `MIT` | [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy) | Plugin and hook management for pytest. |
| **iniconfig** | `>=2.0.0` | MIT | `MIT` | [pytest-dev/iniconfig](https://github.com/pytest-dev/iniconfig) | Lightweight INI configuration parser for pytest. |
| **ruff** | `>=0.9.0` | MIT OR Apache-2.0 | `MIT OR Apache-2.0` | [astral-sh/ruff](https://github.com/astral-sh/ruff) | High-performance Python linter and code formatter. |
| **PyInstaller** | `>=6.0` | GPL-2.0-or-later WITH Bootloader-exception | `GPL-2.0-or-later WITH Bootloader-exception` | [pyinstaller/pyinstaller](https://github.com/pyinstaller/pyinstaller) | Multiplatform executable freezing engine with special exception permitting permissive payloads. |
| **Pillow** | `>=12.3.0` | HPND-sell-variant | `HPND-sell-variant` | [python-pillow/Pillow](https://github.com/python-pillow/Pillow) | Multi-resolution application icon generation and preview asset rendering. |
| **altgraph** | `>=0.17.4` | MIT | `MIT` | [ronaldoussoren/altgraph](https://github.com/ronaldoussoren/altgraph) | Python graph construction and traversal module used internally by PyInstaller. |
| **pyinstaller-hooks-contrib** | `>=2024.0` | Apache-2.0 | `Apache-2.0` | [pyinstaller/pyinstaller-hooks-contrib](https://github.com/pyinstaller/pyinstaller-hooks-contrib) | Community hooks repository for PyInstaller package bundling. |
| **packaging** | `>=24.0` | Apache-2.0 OR BSD-2-Clause | `Apache-2.0 OR BSD-2-Clause` | [pypa/packaging](https://github.com/pypa/packaging) | Core Python packaging interoperability and version parsing utilities. |

---

## Licensing Architecture, Dynamic Linking & Unprivileged Execution

### Dynamic Linking & LGPL-3.0 Isolation
- **CloudLockFixer Core:** All application code, queue parsers, state machines, provider sensors, CLI entrypoints, and worker engines are licensed under the permissive [MIT License](LICENSE).
- **PySide6 (LGPL-3.0-only):** The Qt 6 bindings and Qt runtime binaries are linked dynamically via official CPython wheels. In frozen binary distributions (PyInstaller), Qt libraries reside as separate shared objects / DLLs (`Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`), permitting end users to replace the Qt library binaries in compliance with LGPL-3.0 Section 4.
- **Zero-Copyleft Contamination:** The application codebase contains no GPL or AGPL proprietary-restricting source code. The PyInstaller bootloader exception expressly permits combining with the application without viral licensing effects.

### Unprivileged User-Mode Operation (`RunAsInvoker`)
- All CloudLockFixer processes (`clf_app.py`, `clf_launcher.pyw`, CLI invocation `cloudlockfixer.cli`, and background worker threads) execute strictly in **unprivileged user mode** (`RunAsInvoker`).
- No administrative elevation, UAC prompt, or root capabilities are ever required or requested.
- Configuration and logs reside safely within the user profile directory (`%LOCALAPPDATA%\CloudLockFixer` on Windows, `~/.local/share/CloudLockFixer` on Linux, or `~/Library/Application Support/CloudLockFixer` on macOS).
- Autostart and context menu entries live strictly within the user domain (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, `~/.config/autostart`, or `~/Library/LaunchAgents`).

---

## Governance & Runtime Invariants

`CloudLockFixer` adheres to ten foundational governance and runtime invariants:

| Invariant | Category | Description | Verification Method |
|---|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero Egress | 100% offline-first execution; zero telemetry, analytics, or unsolicited network sockets. | `tests/test_metadata.py` & `tests/test_zero_egress.py` |
| `INV-RUNAS-02` | Unprivileged User Mode (`RunAsInvoker`) | Strictly unprivileged execution; no UAC or root prompts required. | `SECURITY.md` & `pyproject.toml` |
| `INV-HASH-03` | Cryptographic Copy+Delete Fallback | Bit-for-bit SHA-256 digest verification before source unlinking; zero data loss. | `tests/test_copy_delete.py` & `src/cloudlockfixer/ops.py` |
| `INV-CHAIN-04` | Atomic Multi-Step Chains | Sequential 1–4 step execution (`rename`, `move`, `delete`); failure immediately halts downstream steps. | `tests/test_operations.py` & `tests/test_queue.py` |
| `INV-SENSOR-05` | Multi-Cloud Engine Sensor | Intelligent detection of 8 providers; pauses folder sync only on repeated failures; virtual mounts never paused. | `tests/test_providers_multi.py` & `tests/test_review_fixes_2026_07_12.py` |
| `INV-IDEMP-06` | Deterministic Idempotent Retry | Safe re-execution of tasks across `pending`, `retryable`, `blocked`, and `done` states without data duplication. | `tests/test_retry.py` & `tests/test_worker.py` |
| `INV-TRIM-07` | Defensive Source & Read-Only Handling | Automatic clearing of read-only flags prior to deletion; case-only renames preserved on case-insensitive filesystems. | `tests/test_audit_fixes.py` & `tests/test_operations.py` |
| `INV-PLAT-08` | Cross-Platform Foundation | Cross-platform abstractions and autostart support across Windows, Linux, and macOS. | `tests/test_providers_cross_platform.py` & `tests/source_platform_smoke.py` |
| `INV-DOCS-09` | 1:1 Bilingual Documentation | Symmetrical 18-point documentation parity across English (`README.md`) and German (`README.de.md`) backed by `llms.txt`. | `tests/test_metadata.py` |
| `INV-SLA-10` | Open Source Governance & SLA | MIT License, public GitHub issue tracker, and committed 48h initial response / 5d triage security SLA. | `SECURITY.md` & `tests/test_security_license_contract.py` |

---

## License Texts & Attribution

### MIT License (`CloudLockFixer`, `pytest`, `ruff`, `altgraph`, `iniconfig`, `pluggy`)

```
MIT License

Copyright (c) 2026 file-bricks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
