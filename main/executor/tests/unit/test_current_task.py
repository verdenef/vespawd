"""CURRENT TASK parser tests (§4.4)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.current_task import parse_current_task
from vespawd_executor.parse.sections import get_section, split_sections

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_sample_current_task() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    body = get_section(section_map.sections, "CURRENT TASK")
    task, errors = parse_current_task(body)
    assert errors == []
    assert task is not None
    assert task.status == "in_progress"
    assert "MVP scope" in task.goal
    assert len(task.acceptance_items) == 2
    assert "software.scope" in task.notes or "scope" in task.notes.lower()


def test_missing_goal() -> None:
    body = "Status: in_progress\n\n### Acceptance criteria\n\n- [ ] x\n"
    task, errors = parse_current_task(body)
    assert task is None
    assert any("Goal" in e for e in errors)


def test_missing_acceptance_checkboxes() -> None:
    body = "Status: in_progress\n\n### Goal\n\nDo thing\n\n### Acceptance criteria\n\nNo checkboxes\n"
    task, errors = parse_current_task(body)
    assert task is None
    assert any("checkbox" in e for e in errors)
