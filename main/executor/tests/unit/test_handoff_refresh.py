"""HANDOFF full refresh unit tests (§13, §5.4 step 4)."""

from __future__ import annotations

from datetime import datetime, timezone

from vespawd_executor.parse.types import ContextUpdatesParsed, CurrentTaskParsed
from vespawd_executor.sync.handoff import (
    HandoffFacts,
    handoff_facts_from_task,
    refresh_handoff,
)

TS = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)


def _task(criteria: str) -> CurrentTaskParsed:
    return CurrentTaskParsed(
        status="in_progress",
        goal="Build service",
        constraints="",
        acceptance_criteria=criteria,
        notes="",
    )


def test_facts_from_task_splits_checkboxes() -> None:
    task = _task("- [x] login works\n- [ ] logout works\n- [x] session stored")
    ctx = ContextUpdatesParsed(raw="", product_name="CourseReg", database="MySQL")
    facts = handoff_facts_from_task(task, ctx)
    assert facts.features_done == ["login works", "session stored"]
    assert facts.features_pending == ["logout works"]
    assert facts.project_name == "CourseReg"
    assert facts.database == "MySQL"


def test_refresh_fills_empty_sections(tmp_path) -> None:
    path = tmp_path / "HANDOFF_FOR_DOCUMENTER.md"
    facts = HandoffFacts(
        project_name="CourseReg",
        database="MySQL",
        language="Python",
        framework="FastAPI",
        what_built=["Auth service"],
        features_done=["login"],
        features_pending=["logout"],
        testing_steps=["Run pytest"],
        run_commands=["uvicorn app:main"],
        known_limitations=["No rate limiting"],
    )
    _, warnings = refresh_handoff(path, facts, repo_path="/repo", timestamp=TS)
    text = path.read_text(encoding="utf-8")
    assert "Created new" in warnings[0]
    assert "- **Name:** CourseReg" in text
    assert "| Database | MySQL |" in text
    assert "| Language | Python |" in text
    assert "| Framework | FastAPI |" in text
    assert "- [x] login" in text
    assert "- logout" in text
    assert "1. Run pytest" in text
    assert "uvicorn app:main" in text
    assert "- No rate limiting" in text
    assert "_Generated: 2026-07-02T10:00:00Z | Repo: /repo_" in text


def test_refresh_preserves_existing_content(tmp_path) -> None:
    path = tmp_path / "HANDOFF_FOR_DOCUMENTER.md"
    refresh_handoff(
        path,
        HandoffFacts(features_done=["first"]),
        repo_path="/repo",
        timestamp=TS,
    )
    # Second refresh with different facts must not overwrite already-filled section.
    refresh_handoff(
        path,
        HandoffFacts(features_done=["second"]),
        repo_path="/repo",
        timestamp=TS,
    )
    text = path.read_text(encoding="utf-8")
    assert "- [x] first" in text
    assert "- [x] second" not in text


def test_refresh_idempotent(tmp_path) -> None:
    path = tmp_path / "HANDOFF_FOR_DOCUMENTER.md"
    facts = HandoffFacts(project_name="App", features_done=["a"], database="MySQL")
    refresh_handoff(path, facts, repo_path="/repo", timestamp=TS)
    first = path.read_text(encoding="utf-8")
    refresh_handoff(path, facts, repo_path="/repo", timestamp=TS)
    second = path.read_text(encoding="utf-8")
    assert first == second


def test_refresh_empty_facts_scaffolds_only(tmp_path) -> None:
    path = tmp_path / "HANDOFF_FOR_DOCUMENTER.md"
    _, _ = refresh_handoff(path, HandoffFacts(), repo_path="/repo", timestamp=TS)
    text = path.read_text(encoding="utf-8")
    assert "## Features implemented" in text
    assert "## Testing / demo" in text
