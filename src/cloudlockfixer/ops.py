"""Dateisystem-Operationen — plattformneutral.

Kernidee: rename/move zuerst als schnelles os.replace versuchen; scheitert das
am Cloud-Files-Filter (cldflt) mit Zugriff-verweigert/EXDEV, automatisch auf
copy+delete ausweichen (der MS-empfohlene, filter-sichere Workaround).

Idempotenz fuer verzoegerte Retries: Wenn der Copy-Teil gelang, aber das
Loeschen der Quelle (noch) gesperrt ist, merkt sich der Schritt das via
`Step.copied` — der naechste Lauf loescht dann nur noch die Quelle und kopiert
NICHT erneut (kein Datenverlust, kein Doppel-Copy).
"""
from __future__ import annotations

import errno as _errno
import os
import shutil
import stat
import sys
from pathlib import Path

from .models import Step, Task

# Fehlercodes, die auf einen temporären Lock hinweisen und einen Retry erlauben.
# EBUSY (16): Datei von anderem Prozess gehalten (Cloud-Sync, Antivirus, …)
# EPERM (1) / EACCES (13): Zugriff verweigert (read-only, Cloud-Filter cldflt)
# EXDEV (18): Cross-Device-Rename — immer über copy+delete lösen
_LOCK_ERRNOS: frozenset[int] = frozenset([
    _errno.EBUSY,
    _errno.EPERM,
    _errno.EACCES,
    _errno.EXDEV,
])


def _is_lock_error(e: OSError) -> bool:
    """True wenn der Fehler auf einen temporären Lock hindeutet (Retry sinnvoll)."""
    if e.errno in _LOCK_ERRNOS:
        return True
    # Windows-spezifisch: WinError 32 (Sharing-Verletzung), 33 (Lock-Verletzung)
    win_err = getattr(e, "winerror", None)
    return win_err in (32, 33)


def _force_writable(path: str | os.PathLike) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass


def _on_rm_error(func, path, _exc):
    """rmtree-Fehlerbehandler: read-only-Attribut entfernen, dann erneut versuchen.
    Windows verweigert das Loeschen read-only markierter Dateien/Verzeichnisse mit
    WinError 5 (z.B. .pytest_cache, .git/objects oder von OneDrive 'pinned'). Ohne
    diesen Handler bricht shutil.rmtree an solchen Eintraegen ab."""
    _force_writable(path)
    func(path)


def _rmtree(p: Path) -> None:
    # onexc ab 3.12 (onerror dort deprecated); Handler-Signatur ist kompatibel.
    if sys.version_info >= (3, 12):
        shutil.rmtree(p, onexc=_on_rm_error)
    else:
        shutil.rmtree(p, onerror=_on_rm_error)


def _payload_signature(p: Path) -> tuple[int, int]:
    """(Anzahl Dateien, Gesamtgroesse) — nur als Sanity-Verify direkt nach Copy."""
    if p.is_file():
        return (1, p.stat().st_size)
    n = total = 0
    for f in p.rglob("*"):
        if f.is_file():
            n += 1
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return (n, total)


def _verify_copy(src: Path, dst: Path) -> bool:
    try:
        return dst.exists() and _payload_signature(src) == _payload_signature(dst)
    except OSError:
        return False


def _delete_path(p: Path) -> tuple[bool, str]:
    try:
        if not p.exists():
            return True, "bereits geloescht"
        if p.is_dir():
            try:
                _rmtree(p)
            except OSError as e:
                if _is_lock_error(e):
                    # Bug 3: Verzeichnis mit gesperrter Innendatei
                    ok, locked = _delete_dir_skip_locked(p)
                    if ok:
                        return True, "geloescht (gesperrte Innendateien uebersprungen)"
                    if locked:
                        names = ", ".join(str(lp.name) for lp in locked[:3])
                        return False, f"Innendatei(en) noch gesperrt (EBUSY): {names}"
                    # Bug 4: leeres Verzeichnis, aber sein eigenes Handle ist gesperrt
                    return False, (
                        "Verzeichnis-Handle selbst gesperrt (offenes Handle, "
                        "z.B. Windows Search-Indexer) -- Retry"
                    )
                raise
        else:
            try:
                p.unlink()
            except OSError:
                _force_writable(p)  # read-only Datei -> beschreibbar machen
                p.unlink()
        return True, "geloescht"
    except OSError as e:
        return False, f"Loeschen fehlgeschlagen: {e}"


def _delete_dir_skip_locked(p: Path) -> tuple[bool, list[Path]]:
    """Löscht ein Verzeichnis rekursiv, überspringt EBUSY-gesperrte Dateien.

    Gibt zurück: (vollständig_gelöscht, [gesperrte_Pfade]).
    Wird genutzt wenn _rmtree() wegen gesperrter Innendatei scheitert, damit
    zumindest alle nicht-gesperrten Dateien bereinigt werden (Bug 3 aus TODO.md).
    """
    locked: list[Path] = []
    if not p.exists():
        return True, []

    # Dateien zuerst (tiefes Niveau zuerst damit Verzeichnisse leer werden)
    for child in sorted(p.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if child.is_file() or child.is_symlink():
            try:
                _force_writable(child)
                child.unlink()
            except OSError as e:
                if _is_lock_error(e):
                    locked.append(child)
                # Andere Fehler ignorieren (best-effort)

    # Leere Unterverzeichnisse entfernen
    for child in sorted(p.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if child.is_dir():
            try:
                child.rmdir()  # nur wenn leer
            except OSError:
                pass

    if not locked:
        try:
            p.rmdir()
        except OSError:
            pass

    # Bug 4: Erfolg am echten FS-Zustand messen, nicht an `locked`. Ein leeres
    # Verzeichnis, dessen EIGENES Handle gesperrt ist (z.B. Windows Search-Indexer),
    # hat KEINE gesperrte Innendatei -> locked bliebe [] und das oben verschluckte
    # p.rmdir()-OSError wuerde faelschlich als Erfolg gewertet. Re-Check verhindert
    # das stille "completed", sodass der Worker den Task korrekt erneut versucht.
    return (not p.exists()), locked


def _do_move(src: Path, dst: Path) -> tuple[bool, str, bool]:
    """Verschiebt src -> dst. Rueckgabe: (ok, msg, copied).
    `copied`=True heisst: dst ist vollstaendig erstellt (egal ob Quelle schon weg).
    Ziel-existiert (mit anderem Inhalt als 'schon erledigt') = Konflikt -> Fehler."""
    if not src.exists() and dst.exists():
        return True, "bereits verschoben", True
    if not src.exists():
        return False, f"Quelle fehlt: {src}", False
    if dst.exists():
        return False, f"Ziel existiert bereits (Konflikt): {dst}", False
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"Zielordner nicht anlegbar: {e}", False

    # 1) Schneller in-place-Versuch (klappt ausserhalb gesperrter Cloud-Ordner)
    try:
        os.replace(src, dst)
        return True, "in-place verschoben", False  # Quelle ist schon weg
    except OSError:
        pass  # Fallback auf copy+delete (deckt EBUSY, EPERM, EACCES, EXDEV ab)

    # 2) copy+delete (filter-sicher)
    try:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    except OSError as e:
        if dst.exists() and not _verify_copy(src, dst):
            _delete_path(dst)  # unvollstaendiges Ziel entfernen -> sauberer Retry
        return False, f"Copy fehlgeschlagen: {e}", False

    if not _verify_copy(src, dst):
        _delete_path(dst)
        return False, "Copy unvollstaendig (Verify fehlgeschlagen)", False

    ok, msg = _delete_path(src)
    if ok:
        return True, "verschoben (copy+delete)", True
    return False, f"Kopiert, aber Quelle noch gesperrt — Retry spaeter ({msg})", True


# ── Standalone-API (fuer direkte Nutzung/Tests) ─────────────────────

def move_path(src: Path | str, dst: Path | str) -> tuple[bool, str]:
    ok, msg, _ = _do_move(Path(src), Path(dst))
    return ok, msg


def rename_path(src: Path | str, new_name: str) -> tuple[bool, str]:
    if "/" in new_name or "\\" in new_name:
        return False, "Neuer Name darf keinen Pfad enthalten"
    src = Path(src)
    ok, msg, _ = _do_move(src, src.parent / new_name)
    return ok, msg


# ── Schritt-/Ketten-Ausfuehrung (mit Idempotenz via Step.copied) ────

def _move_step(step: Step, dst: Path) -> tuple[bool, str]:
    src = Path(step.src)
    if step.copied and dst.exists():
        # Copy war schon erfolgreich -> nur noch Quelle loeschen
        if src.exists():
            ok, msg = _delete_path(src)
            return ok, ("Quelle nach Copy entfernt" if ok else msg)
        return True, "bereits verschoben"
    ok, msg, copied = _do_move(src, dst)
    if copied:
        step.copied = True
    return ok, msg


def execute_step(step: Step) -> tuple[bool, str]:
    if step.op == "rename":
        if "/" in step.arg or "\\" in step.arg:
            return False, "Neuer Name darf keinen Pfad enthalten"
        return _move_step(step, Path(step.src).parent / step.arg)
    if step.op == "move":
        return _move_step(step, Path(step.arg))
    if step.op == "delete":
        return _delete_path(Path(step.src))
    return False, f"Unbekannte Operation: {step.op}"


def execute_chain(task: Task) -> bool:
    """Fuehrt die Kette ab task.step_index aus. Schritt N nur nach Erfolg N-1."""
    for i in range(task.step_index, len(task.chain)):
        ok, msg = execute_step(task.chain[i])
        if ok:
            task.step_index = i + 1
            continue
        task.last_error = f"Schritt {i + 1} ({task.chain[i].describe()}): {msg}"
        return False
    task.status = "done"
    task.last_error = ""
    return True
