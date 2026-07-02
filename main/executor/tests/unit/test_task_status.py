"""current_task Status close-out helper tests (§10.6)."""

from __future__ import annotations

from vespawd_executor.sync.current_task import set_task_status


def test_updates_status(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n\n**Status:** `in_progress`\n\n## Goal\n\nX\n", encoding="utf-8")
    _, changed = set_task_status(path, "idle")
    assert changed
    assert "**Status:** `idle`" in path.read_text(encoding="utf-8")


def test_idempotent_when_already_target(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("**Status:** `idle`\n", encoding="utf-8")
    _, changed = set_task_status(path, "idle")
    assert changed is False


def test_missing_file_noop(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    _, changed = set_task_status(path, "idle")
    assert changed is False


def test_no_status_line_noop(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n\n## Goal\n\nX\n", encoding="utf-8")
    _, changed = set_task_status(path, "idle")
    assert changed is False
