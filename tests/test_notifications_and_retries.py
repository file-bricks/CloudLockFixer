from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from cloudlockfixer import cli, settings, tray


def test_settings_retry_and_notifications_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()
    assert cfg["interval_min"] == 120
    assert settings.get_max_retries(cfg) is None
    assert settings.get_notifications_enabled(cfg) is True


def test_settings_retry_limit_persistence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()
    settings.set_max_retries(cfg, 5)

    loaded = settings.load()
    assert loaded["max_retries"] == 5
    assert settings.get_max_retries(loaded) == 5

    # Reset to unlimited
    settings.set_max_retries(loaded, None)
    reloaded = settings.load()
    assert reloaded["max_retries"] is None
    assert settings.get_max_retries(reloaded) is None


def test_settings_set_max_retries_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()
    with pytest.raises(ValueError):
        settings.set_max_retries(cfg, 0)
    with pytest.raises(ValueError):
        settings.set_max_retries(cfg, -3)
    with pytest.raises(ValueError):
        settings.set_max_retries(cfg, "invalid")  # type: ignore[arg-type]


def test_settings_notifications_persistence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    cfg = settings.load()
    settings.set_notifications_enabled(cfg, False)

    loaded = settings.load()
    assert loaded["notifications_enabled"] is False
    assert settings.get_notifications_enabled(loaded) is False

    settings.set_notifications_enabled(loaded, True)
    reloaded = settings.load()
    assert reloaded["notifications_enabled"] is True
    assert settings.get_notifications_enabled(reloaded) is True


def test_cli_run_now_passes_explicit_max_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)

    captured_kwargs: dict[str, object] = {}

    def fake_run_once(queue, force_pause=False, max_retries=None):
        captured_kwargs["force_pause"] = force_pause
        captured_kwargs["max_retries"] = max_retries
        return {
            "done": 1,
            "failed_again": 0,
            "failed_permanent": 0,
            "pending_start": 0,
            "paused_providers": [],
        }

    monkeypatch.setattr(cli, "run_once", fake_run_once)

    ret = cli.main(["run-now", "--max-retries", "7"])
    assert ret == 0
    assert captured_kwargs["max_retries"] == 7
    assert captured_kwargs["force_pause"] is False


def test_cli_run_now_uses_configured_max_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)

    cfg = settings.load()
    settings.set_max_retries(cfg, 4)

    captured_kwargs: dict[str, object] = {}

    def fake_run_once(queue, force_pause=False, max_retries=None):
        captured_kwargs["max_retries"] = max_retries
        return {
            "done": 0,
            "failed_again": 0,
            "failed_permanent": 0,
            "pending_start": 0,
            "paused_providers": [],
        }

    monkeypatch.setattr(cli, "run_once", fake_run_once)

    ret = cli.main(["run-now"])
    assert ret == 0
    assert captured_kwargs["max_retries"] == 4


def test_tray_notifications_on_permanent_failure_and_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    monkeypatch.setattr(tray, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tray, "available_providers", lambda: [])

    tray_app = tray.TrayApp(app)
    messages: list[tuple[str, str]] = []

    def fake_show_message(title, msg, icon=None, msecs=0):
        messages.append((title, msg))

    monkeypatch.setattr(tray_app.tray, "showMessage", fake_show_message)

    # 1. Success message
    tray_app._on_done({"done": 3})
    assert len(messages) == 1
    assert "3" in messages[0][1]

    # 2. Permanent failure notification
    messages.clear()
    tray_app._on_done({"done": 0, "failed_permanent": 2, "blocked": 0})
    assert len(messages) == 1
    assert "2" in messages[0][1]

    # 3. Blocked notification
    messages.clear()
    tray_app._on_done({"done": 0, "failed_permanent": 0, "blocked": 1})
    assert len(messages) == 1
    assert "1" in messages[0][1]

    # 4. Both permanent and blocked
    messages.clear()
    tray_app._on_done({"done": 0, "failed_permanent": 2, "blocked": 1})
    assert len(messages) == 1
    assert "3" in messages[0][1]

    # 5. Notifications disabled
    messages.clear()
    tray_app._toggle_notifications(False)
    tray_app._on_done({"done": 1, "failed_permanent": 2, "blocked": 1})
    assert len(messages) == 0


def test_tray_set_max_retries_method(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    monkeypatch.setattr(tray, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tray, "available_providers", lambda: [])

    tray_app = tray.TrayApp(app)
    tray_app._set_max_retries(10)

    loaded = settings.load()
    assert loaded["max_retries"] == 10
