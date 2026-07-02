"""Idempotency tests (§11.4)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.api.invoke import invoke

from tests.integration.conftest import requires_vedaws


@requires_vedaws
def test_bootstrap_idempotent_three_times(bridge_context) -> None:
    for _ in range(3):
        result = invoke("bootstrap", bridge_context, {})
        assert result.ok, result.blockers


@requires_vedaws
def test_sync_status_stable_except_last_sync(fixture_workspace: Path, bridge_context) -> None:
    invoke("bootstrap", bridge_context, {})
    snapshots = []
    for _ in range(5):
        result = invoke("sync_status", bridge_context, {})
        assert result.ok
        text = (fixture_workspace / "paws022" / "tasks" / "status.md").read_text(encoding="utf-8")
        snapshots.append(text)
    normalized = [s.split("Last_sync")[0] for s in snapshots]
    assert len(set(normalized)) == 1


@requires_vedaws
def test_ingest_idempotent_no_duplicate_notes(fixture_workspace: Path, bridge_context) -> None:
    invoke("bootstrap", bridge_context, {})
    payload = {
        "current_task": {
            "goal": "Implement the feature",
            "acceptance_criteria": "- [ ] done",
        },
        "phase_hint": "implement",
    }
    invoke("ingest_master_prompt", bridge_context, payload)
    invoke("ingest_master_prompt", bridge_context, payload)
    notes = (fixture_workspace / "paws022" / "tasks" / "current_task.md").read_text(encoding="utf-8")
    assert notes.count("**Vedaws phase:**") == 1
