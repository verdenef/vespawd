"""current_task.md writer tests (§4.4)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from vespawd_executor.parse.current_task import parse_current_task
from vespawd_executor.parse.sections import get_section, split_sections
from vespawd_executor.sync.current_task import render_current_task, write_current_task

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")


def _sample_task():
    section_map, _ = split_sections(SAMPLE)
    task, errors = parse_current_task(get_section(section_map.sections, "CURRENT TASK"))
    assert not errors and task
    return task


def test_render_current_task_format() -> None:
    task = _sample_task()
    text = render_current_task(task, phase_hint="scope", started="2026-06-01")
    assert "**Status:** `in_progress`" in text
    assert "**Started:** 2026-06-01" in text
    assert "## Goal" in text
    assert "## Acceptance Criteria" in text
    assert "Vedaws phase: software.scope" in text


def test_write_preserves_started_for_same_goal(tmp_path: Path) -> None:
    path = tmp_path / "current_task.md"
    task = _sample_task()
    write_current_task(path, task, phase_hint="scope", started_at=date(2026, 6, 1))
    write_current_task(path, task, phase_hint="scope")
    text = path.read_text(encoding="utf-8")
    assert "**Started:** 2026-06-01" in text


def test_write_idempotent_content(tmp_path: Path) -> None:
    path = tmp_path / "current_task.md"
    task = _sample_task()
    write_current_task(path, task, phase_hint="scope", started_at=date(2026, 6, 1))
    first = path.read_text(encoding="utf-8")
    write_current_task(path, task, phase_hint="scope", started_at=date(2026, 6, 1))
    assert path.read_text(encoding="utf-8") == first


def test_instruction_conflicts_in_notes() -> None:
    task = _sample_task()
    text = render_current_task(
        task,
        instruction_conflicts=["acceptance criteria win on scope"],
        started="2026-06-01",
    )
    assert "Executor note: acceptance criteria win" in text
