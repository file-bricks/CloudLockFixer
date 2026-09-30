from __future__ import annotations

import json

import pytest

from cloudlockfixer import cli
from cloudlockfixer.legacy_retry import review_legacy_retries


def _task(**changes):
    return {
        "id": "legacy", "status": "failed", "retry_count": 5,
        "last_error": "Nach 5 Fehlversuchen aufgegeben: Zugriff verweigert",
        "last_outcome": "retryable", "step_index": 1,
        "chain": [{"op": "move", "copied": True}], **changes,
    }


def test_review_preserves_progress_and_requires_decision(tmp_path):
    path = tmp_path / "queue.json"
    tasks = [_task(), _task(id="deliberate-limit")]
    path.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
    before = path.read_bytes(), path.stat().st_mtime_ns
    report = review_legacy_retries(path)
    assert report["candidate_count"] == 2
    assert report["requires_user_decision"] is True
    assert "indistinguishable" in report["reason"]
    candidate = report["candidates"][0]
    for key in ("last_error", "last_outcome", "step_index", "chain"):
        assert candidate[key] == tasks[0][key]
    assert candidate["retry_argv"] == ["clf", "retry", "legacy"]
    assert len(report["queue_sha256"]) == 64
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize("changes", [
    {"status": "pending"}, {"status": "blocked"},
    {"retry_count": 4}, {"retry_count": 6},
    {"retry_count": "5"}, {"retry_count": 5.0},
])
def test_review_excludes_other_states(tmp_path, changes):
    path = tmp_path / "queue.json"
    path.write_text(json.dumps({"tasks": [_task(**changes)]}), encoding="utf-8")
    assert review_legacy_retries(path)["candidate_count"] == 0


def test_cli_review_does_not_load_settings_ingest_queue_or_log(tmp_path, monkeypatch, capsys):
    path = tmp_path / "queue.json"
    path.write_text(json.dumps({"tasks": [_task()]}), encoding="utf-8")
    inbox = tmp_path / "queue.txt"
    inbox.write_text("delete C:/important\n", encoding="utf-8")
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}

    def forbidden(*args, **kwargs):
        pytest.fail("read-only review invoked a mutating service")

    monkeypatch.setattr(cli.settings, "load", forbidden)
    monkeypatch.setattr(cli, "_setup_logging", forbidden)
    monkeypatch.setattr(cli, "Queue", forbidden)
    assert cli.main(["review-legacy-retries", "--queue", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["candidate_count"] == 1
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()} == before


@pytest.mark.parametrize("payload", [
    "invalid JSON", "[]", '{"tasks": {}}', '{"tasks": [null]}',
    json.dumps({"tasks": [_task(id="")]}),
    json.dumps({"tasks": [_task(), _task()]}),
])
def test_cli_review_rejects_invalid_or_ambiguous_queue(tmp_path, capsys, payload):
    path = tmp_path / "queue.json"
    path.write_text(payload, encoding="utf-8")
    assert cli.main(["review-legacy-retries", "--queue", str(path)]) == 2
    output = capsys.readouterr()
    assert not output.out
    assert output.err
    assert path.read_text(encoding="utf-8") == payload


def test_cli_missing_queue_creates_no_directory(tmp_path, capsys):
    path = tmp_path / "absent" / "queue.json"
    assert cli.main(["review-legacy-retries", "--queue", str(path)]) == 2
    assert not path.parent.exists()
    assert capsys.readouterr().err
