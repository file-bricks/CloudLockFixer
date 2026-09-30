"""Read-only review of failures potentially caused by the old five-attempt cap."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def review_legacy_retries(queue_path: Path) -> dict:
    """List candidates without loading Queue or changing either queue file.

    Old queues do not record whether a five-attempt limit was deliberate.
    Every candidate therefore requires a user's decision before retrying.
    """
    raw = queue_path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
        raise ValueError("queue.json must contain a tasks list")
    seen = set()
    candidates = []
    for task in payload["tasks"]:
        if not isinstance(task, dict):
            raise ValueError("queue tasks must be objects")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in seen:
            raise ValueError("queue task IDs must be nonempty and unique")
        seen.add(task_id)
        if task.get("status") != "failed" or type(task.get("retry_count")) is not int:
            continue
        if task["retry_count"] != 5:
            continue
        candidates.append({
            "id": task_id,
            "last_error": task.get("last_error", ""),
            "last_outcome": task.get("last_outcome", ""),
            "step_index": task.get("step_index", 0),
            "chain": task.get("chain", []),
            "retry_argv": ["clf", "retry", task_id],
        })
    return {
        "queue_path": str(queue_path),
        "queue_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_count": len(candidates),
        "requires_user_decision": True,
        "reason": "legacy_default_and_explicit_five_attempt_limits_are_indistinguishable",
        "candidates": candidates,
    }
