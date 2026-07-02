"""Integration tests — ingest, gates, phase complete, documenter (§11.2)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.api.invoke import invoke

from tests.integration.conftest import requires_vedaws


@requires_vedaws
def test_ingest_sync_pre_implement(bridge_context) -> None:
    invoke("bootstrap", bridge_context, {})
    ingest = invoke(
        "ingest_master_prompt",
        bridge_context,
        {
            "current_task": {
                "goal": "Implement the feature",
                "acceptance_criteria": "- [ ] works",
            },
            "phase_hint": "implement",
        },
    )
    assert ingest.ok, ingest.blockers
    assert ingest.vedaws_task_id == "software.implement"

    sync = invoke("sync_status", bridge_context, {})
    assert sync.ok

    gate = invoke(
        "pre_implement_check",
        bridge_context,
        {"current_task": "Implement the backend service logic"},
    )
    assert gate.ok, gate.blockers


@requires_vedaws
def test_post_phase_complete(bridge_context) -> None:
    invoke("bootstrap", bridge_context, {})
    invoke(
        "ingest_master_prompt",
        bridge_context,
        {
            "current_task": {
                "goal": "Scope the MVP",
                "acceptance_criteria": "- [ ] defined",
            },
            "phase_hint": "scope",
        },
    )
    result = invoke(
        "post_phase_complete",
        bridge_context,
        {
            "vedaws_task_id": "software.scope",
            "outcome": "completed",
            "human_gate": True,
        },
    )
    assert result.ok, result.blockers
    assert any("tasks" in cmd for cmd in result.vedaws_commands_run)

    next_ingest = invoke(
        "ingest_master_prompt",
        bridge_context,
        {
            "current_task": {
                "goal": "Design the system architecture",
                "acceptance_criteria": "- [ ] ADR drafted",
            },
            "phase_hint": "architecture",
        },
    )
    assert next_ingest.ok, next_ingest.blockers
    assert next_ingest.vedaws_task_id == "software.architecture"


@requires_vedaws
def test_pre_documenter(bridge_context, fixture_workspace: Path) -> None:
    invoke("bootstrap", bridge_context, {})
    main = fixture_workspace / "main"
    (main / "docs" / "architecture" / "ARCHITECTURE.md").parent.mkdir(parents=True, exist_ok=True)
    (main / "docs" / "architecture" / "ARCHITECTURE.md").write_text("# Arch\n", encoding="utf-8")
    (main / "docs" / "api" / "API.md").parent.mkdir(parents=True, exist_ok=True)
    (main / "docs" / "api" / "API.md").write_text("# API\n", encoding="utf-8")

    result = invoke("pre_documenter", bridge_context, {})
    assert "doctor" in " ".join(result.vedaws_commands_run)
    assert "software" in " ".join(result.vedaws_commands_run)
