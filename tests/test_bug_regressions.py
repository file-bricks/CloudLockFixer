"""Regressionstests — bugfix-library-transfer 2026-06-21."""
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "cloudlockfixer"
TRAY = SRC / "tray.py"


class TestD2NoDeprecatedEnums(unittest.TestCase):
    """BUG-D2: Deprecated Qt/QPainter-Enums in PySide6 6.4+."""

    def _src(self):
        return TRAY.read_text(encoding="utf-8")

    def test_no_qt_transparent_bare(self):
        self.assertNotIn(
            "Qt.transparent",
            self._src(),
            "Qt.transparent (deprecated bare) in tray.py — BUG-D2",
        )

    def test_no_qpainter_antialiasing_bare(self):
        self.assertNotIn(
            "QPainter.Antialiasing",
            self._src(),
            "QPainter.Antialiasing (deprecated bare) in tray.py — BUG-D2",
        )

    def test_no_qt_nopen_bare(self):
        self.assertNotIn(
            "Qt.NoPen",
            self._src(),
            "Qt.NoPen (deprecated bare) in tray.py — BUG-D2",
        )

    def test_no_qt_aligncenter_bare(self):
        self.assertNotIn(
            "Qt.AlignCenter",
            self._src(),
            "Qt.AlignCenter (deprecated bare) in tray.py — BUG-D2",
        )


if __name__ == "__main__":
    unittest.main()
