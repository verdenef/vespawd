"""current_task Notes appender tests (§11.5, §12.5)."""

from __future__ import annotations

from vespawd_executor.sync.notes import append_task_note

_TASK = """# Current Task

**Status:** `in_progress`

## Goal

Build service

## Notes

-

## Progress Log

| Date | Update |
|------|--------|
"""


def test_appends_note_replacing_placeholder(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text(_TASK, encoding="utf-8")
    _, appended = append_task_note(path, "vedaws CLI missing; orchestration offline")
    assert appended
    text = path.read_text(encoding="utf-8")
    assert "- Executor note: vedaws CLI missing; orchestration offline" in text
    # Placeholder dash removed, Progress Log preserved.
    assert "## Progress Log" in text
    assert text.count("\n-\n") == 0


def test_idempotent_same_note(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text(_TASK, encoding="utf-8")
    _, first = append_task_note(path, "doctor failed")
    _, second = append_task_note(path, "doctor failed")
    assert first is True
    assert second is False
    text = path.read_text(encoding="utf-8")
    assert text.count("Executor note: doctor failed") == 1


def test_custom_prefix(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text(_TASK, encoding="utf-8")
    append_task_note(path, "tried null check", prefix="Debugging")
    assert "- Debugging: tried null check" in path.read_text(encoding="utf-8")


def test_creates_notes_section_when_missing(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n\n## Goal\n\nX\n", encoding="utf-8")
    _, appended = append_task_note(path, "orchestration error recorded")
    assert appended
    text = path.read_text(encoding="utf-8")
    assert "## Notes" in text
    assert "- Executor note: orchestration error recorded" in text


def test_empty_note_noop(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text(_TASK, encoding="utf-8")
    _, appended = append_task_note(path, "   ")
    assert appended is False


def test_missing_file_creates(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    _, appended = append_task_note(path, "note")
    assert appended
    assert path.is_file()
    assert "## Notes" in path.read_text(encoding="utf-8")
