"""Tests for Volume Label Hardening (Task 167 / TW-CLF-05).

Verifies robust volume label detection against real Windows labels,
letter input variations, drive-type filters, network drive resiliency,
and invariant enforcement (preventing false-positive process kills).
"""
import ctypes
import sys
from pathlib import Path

from cloudlockfixer.providers import (
    _DRIVE_FIXED,
    _DRIVE_REMOTE,
    _GOOGLE_DRIVE_VOLUME_LABELS,
    _PCLOUD_VOLUME_LABELS,
    GoogleDriveProvider,
    PCloudProvider,
    _get_volume_label,
    _normalize_volume_label,
    _volume_label_matches,
)


class _FakeKernel32Extended:
    """Mock kernel32 DLL for testing GetDriveTypeW and GetVolumeInformationW."""

    def __init__(
        self,
        drive_type: int = _DRIVE_FIXED,
        label: str = "Google Drive",
        ok: int = 1,
        raise_exc: Exception | None = None,
    ):
        self._drive_type = drive_type
        self._label = label
        self._ok = ok
        self._raise_exc = raise_exc
        self.set_error_mode_calls: list[int] = []
        self.get_volume_calls = 0
        self.last_queried_root = ""

    def SetThreadErrorMode(self, new_mode, old_ptr):
        self.set_error_mode_calls.append(new_mode)
        return 1

    def GetDriveTypeW(self, root):
        self.last_queried_root = root
        if self._raise_exc and "drivetype" in str(self._raise_exc).lower():
            raise self._raise_exc
        return self._drive_type

    def GetVolumeInformationW(self, root, buf, size, *rest):
        self.get_volume_calls += 1
        self.last_queried_root = root
        if self._raise_exc:
            raise self._raise_exc
        if self._ok:
            buf.value = self._label
            return 1
        return 0


def _patch_win32_kernel(monkeypatch, fake):
    monkeypatch.setattr(sys, "platform", "win32")

    class _FakeWinDLL:
        kernel32 = fake

    monkeypatch.setattr(ctypes, "windll", _FakeWinDLL(), raising=False)


# ── 1. Label Normalization Tests ──────────────────────────────────────


def test_normalize_volume_label_edge_cases():
    assert _normalize_volume_label("") == ""
    assert _normalize_volume_label(None) == ""
    assert _normalize_volume_label("   ") == ""
    assert _normalize_volume_label("Google Drive") == "google drive"
    assert _normalize_volume_label("  GOOGLE   DRIVE  ") == "google drive"
    # Null bytes from C buffers
    assert _normalize_volume_label("Google Drive\x00\x00") == "google drive"
    # BOM and zero-width spaces
    assert _normalize_volume_label("\ufeffGoogle\u200b Drive\u200c") == "google drive"
    # Unicode non-breaking spaces
    assert _normalize_volume_label("Google\xa0Drive") == "google drive"
    assert _normalize_volume_label("Google\u202fDrive\u3000Data") == "google drive data"


# ── 2. Volume Label Matching Tests ────────────────────────────────────


def test_volume_label_matches_google_drive():
    # Exact matches
    assert _volume_label_matches("Google Drive", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert _volume_label_matches("  GOOGLE   DRIVE  ", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert _volume_label_matches("googledrive", _GOOGLE_DRIVE_VOLUME_LABELS)

    # Drive letter in parentheses (matching)
    assert _volume_label_matches("Google Drive (G:)", _GOOGLE_DRIVE_VOLUME_LABELS, drive_letter="G")
    assert _volume_label_matches("Google Drive (g:)", _GOOGLE_DRIVE_VOLUME_LABELS, drive_letter="g")
    assert _volume_label_matches("GOOGLE DRIVE (G:)", _GOOGLE_DRIVE_VOLUME_LABELS, drive_letter="G")

    # Drive letter mismatch
    assert not _volume_label_matches("Google Drive (H:)", _GOOGLE_DRIVE_VOLUME_LABELS, drive_letter="G")

    # Multi-account Google Drive labels
    assert _volume_label_matches("Google Drive - user@example.com", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert _volume_label_matches("Google Drive - Personal", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert _volume_label_matches("Google Drive - Work", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert not _volume_label_matches("Google Drive - ", _GOOGLE_DRIVE_VOLUME_LABELS)

    # Invariant: Excluded custom labels
    assert not _volume_label_matches("My Google Drive", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert not _volume_label_matches("Google Drive Backup", _GOOGLE_DRIVE_VOLUME_LABELS)
    assert not _volume_label_matches("Google Drive Archive", _GOOGLE_DRIVE_VOLUME_LABELS)


def test_volume_label_matches_pcloud():
    # Exact matches
    assert _volume_label_matches("pCloud Drive", _PCLOUD_VOLUME_LABELS)
    assert _volume_label_matches("  PCLOUD   DRIVE  ", _PCLOUD_VOLUME_LABELS)

    # Drive letter in parentheses (matching)
    assert _volume_label_matches("pCloud Drive (P:)", _PCLOUD_VOLUME_LABELS, drive_letter="P")
    assert _volume_label_matches("pcloud drive (p:)", _PCLOUD_VOLUME_LABELS, drive_letter="p")

    # Drive letter mismatch
    assert not _volume_label_matches("pCloud Drive (Q:)", _PCLOUD_VOLUME_LABELS, drive_letter="P")

    # Invariant: Excluded custom labels
    assert not _volume_label_matches("pCloud", _PCLOUD_VOLUME_LABELS)
    assert not _volume_label_matches("pCloud Archive Disk", _PCLOUD_VOLUME_LABELS)
    assert not _volume_label_matches("My pCloud Drive", _PCLOUD_VOLUME_LABELS)
    assert not _volume_label_matches("pCloud Backup", _PCLOUD_VOLUME_LABELS)


# ── 3. Drive Letter Input Normalization ────────────────────────────────


def test_get_volume_label_drive_letter_normalization(monkeypatch):
    fake = _FakeKernel32Extended(drive_type=_DRIVE_FIXED, label="Google Drive")
    _patch_win32_kernel(monkeypatch, fake)

    # Single letter
    assert _get_volume_label("G") == "Google Drive"
    assert fake.last_queried_root == "G:\\"

    # Lowercase
    assert _get_volume_label("g") == "Google Drive"
    assert fake.last_queried_root == "G:\\"

    # With colon
    assert _get_volume_label("G:") == "Google Drive"
    assert fake.last_queried_root == "G:\\"

    # With trailing backslash
    assert _get_volume_label("G:\\") == "Google Drive"
    assert fake.last_queried_root == "G:\\"

    # With whitespace
    assert _get_volume_label("  g:  ") == "Google Drive"
    assert fake.last_queried_root == "G:\\"

    # Invalid drive letter inputs
    assert _get_volume_label("") == ""
    assert _get_volume_label("1") == ""
    assert _get_volume_label("CDE") == ""
    assert _get_volume_label(None) == ""
    assert _get_volume_label("::") == ""


# ── 4. Drive Type Filtering (Fixed and Remote Allowed, Others Skipped) ──


def test_get_volume_label_drive_type_filters(monkeypatch):
    # FIXED and REMOTE are allowed
    fake_fixed = _FakeKernel32Extended(drive_type=_DRIVE_FIXED, label="Test Fixed")
    _patch_win32_kernel(monkeypatch, fake_fixed)
    assert _get_volume_label("C") == "Test Fixed"
    assert fake_fixed.get_volume_calls == 1

    fake_remote = _FakeKernel32Extended(drive_type=_DRIVE_REMOTE, label="Test Remote")
    _patch_win32_kernel(monkeypatch, fake_remote)
    assert _get_volume_label("Z") == "Test Remote"
    assert fake_remote.get_volume_calls == 1

    # REMOVABLE (2), CDROM (5), RAMDISK (6), UNKNOWN (0), NO_ROOT (1) must be skipped
    for d_type in (0, 1, 2, 5, 6):
        fake_skip = _FakeKernel32Extended(drive_type=d_type, label="Should Not Query")
        _patch_win32_kernel(monkeypatch, fake_skip)
        assert _get_volume_label("D") == ""
        assert fake_skip.get_volume_calls == 0


# ── 5. Netzlaufwerke / Network Resiliency & Error Recovery ─────────────


def test_get_volume_label_network_share_unreachable(monkeypatch):
    # Netzlaufwerk returns ok=0 (e.g. disconnected or permission denied)
    fake_offline = _FakeKernel32Extended(drive_type=_DRIVE_REMOTE, ok=0)
    _patch_win32_kernel(monkeypatch, fake_offline)
    assert _get_volume_label("N") == ""
    assert len(fake_offline.set_error_mode_calls) == 2, "Error mode must be restored"


def test_get_volume_label_network_exception_safely_handled(monkeypatch):
    # Network drive triggers an unexpected OSError
    fake_exc = _FakeKernel32Extended(
        drive_type=_DRIVE_REMOTE,
        raise_exc=OSError("Network connection dropped [WinError 53]"),
    )
    _patch_win32_kernel(monkeypatch, fake_exc)
    assert _get_volume_label("Y") == ""
    assert len(fake_exc.set_error_mode_calls) == 2, "Error mode must be restored on exception"


def test_get_volume_label_null_byte_cleaning(monkeypatch):
    # C string buffer with trailing null bytes and whitespace
    fake_nulls = _FakeKernel32Extended(
        drive_type=_DRIVE_FIXED,
        label="  Google Drive\x00\x00\x00  ",
    )
    _patch_win32_kernel(monkeypatch, fake_nulls)
    assert _get_volume_label("G") == "Google Drive"


# ── 6. End-to-End Provider Root Detection Integration ─────────────────


def test_googledrive_provider_detect_roots_with_hardened_labels(monkeypatch):
    drive_labels = {
        "G": "Google Drive (G:)",
        "H": "Google Drive - testuser@gmail.com",
        "I": "Google Drive Backup",
        "J": "My Google Drive",
    }

    def fake_get_logical_drives(*args, **kwargs):
        mask = 0
        for letter in drive_labels:
            mask |= 1 << (ord(letter) - ord("A"))
        return mask

    def fake_get_volume_label_e2e(letter: str) -> str:
        return drive_labels.get(letter, "")

    monkeypatch.setattr(sys, "platform", "win32")

    class FakeKernel:
        @staticmethod
        def GetLogicalDrives():
            return fake_get_logical_drives()

    class FakeWinDLL:
        kernel32 = FakeKernel()

    monkeypatch.setattr(ctypes, "windll", FakeWinDLL(), raising=False)
    monkeypatch.setattr("cloudlockfixer.providers._get_volume_label", fake_get_volume_label_e2e)
    # Mock Path.home to prevent detecting local folders in user profile
    monkeypatch.setattr(Path, "home", lambda: Path("C:/Users/fake_nonexistent_user"))

    provider = GoogleDriveProvider()
    roots = provider._detect_roots()

    assert Path("G:\\") in roots, "G:\\ with 'Google Drive (G:)' must be detected"
    assert Path("H:\\") in roots, "H:\\ with 'Google Drive - testuser@gmail.com' must be detected"
    assert Path("I:\\") not in roots, "I:\\ with 'Google Drive Backup' must NOT be detected"
    assert Path("J:\\") not in roots, "J:\\ with 'My Google Drive' must NOT be detected"


def test_pcloud_provider_detect_roots_with_hardened_labels(monkeypatch):
    drive_labels = {
        "P": "pCloud Drive (P:)",
        "Q": "pCloud Drive",
        "R": "pCloud Backup",
    }

    def fake_get_logical_drives(*args, **kwargs):
        mask = 0
        for letter in drive_labels:
            mask |= 1 << (ord(letter) - ord("A"))
        return mask

    def fake_get_volume_label_e2e(letter: str) -> str:
        return drive_labels.get(letter, "")

    monkeypatch.setattr(sys, "platform", "win32")

    class FakeKernel:
        @staticmethod
        def GetLogicalDrives():
            return fake_get_logical_drives()

    class FakeWinDLL:
        kernel32 = FakeKernel()

    monkeypatch.setattr(ctypes, "windll", FakeWinDLL(), raising=False)
    monkeypatch.setattr("cloudlockfixer.providers._get_volume_label", fake_get_volume_label_e2e)
    monkeypatch.setattr(Path, "home", lambda: Path("C:/Users/fake_nonexistent_user"))

    provider = PCloudProvider()
    roots = provider._detect_roots()

    assert Path("P:\\") in roots, "P:\\ with 'pCloud Drive (P:)' must be detected"
    assert Path("Q:\\") in roots, "Q:\\ with 'pCloud Drive' must be detected"
    assert Path("R:\\") not in roots, "R:\\ with 'pCloud Backup' must NOT be detected"
