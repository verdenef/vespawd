"""Completed task log unit tests (§5.4 step 5, §10.6)."""

from __future__ import annotations

from datetime import date

from vespawd_executor.sync.completed import completed_log_path, write_completed_log


def test_writes_log(tmp_path) -> None:
    path, created = write_completed_log(
        tmp_path / "completed",
        goal="Implement backend service",
        outcome="completed",
        closed_on=date(2026, 7, 2),
        vedaws_task_id="software.implement",
        acceptance=["login works", "logout works"],
        changed_paths=["main/src/a.py"],
    )
    assert created
    text = (tmp_path / "completed").glob("*.md").__next__().read_text(encoding="utf-8")
    assert "# Completed: Implement backend service" in text
    assert "**Outcome:** completed" in text
    assert "software.implement" in text
    assert "- login works" in text
    assert "- main/src/a.py" in text
    assert "2026-07-02-implement-backend-service" in path


def test_idempotent_same_date_slug(tmp_path) -> None:
    args = dict(goal="Build API", outcome="completed", closed_on=date(2026, 7, 2))
    _, first = write_completed_log(tmp_path / "completed", **args)
    _, second = write_completed_log(tmp_path / "completed", **args)
    assert first is True
    assert second is False
    assert len(list((tmp_path / "completed").glob("*.md"))) == 1


def test_slug_fallback_for_empty_goal(tmp_path) -> None:
    path = completed_log_path(tmp_path / "completed", "!!!", closed_on=date(2026, 7, 2))
    assert path.name == "2026-07-02-task.md"


def test_empty_acceptance_and_changed(tmp_path) -> None:
    path, _ = write_completed_log(
        tmp_path / "completed", goal="X", outcome="completed", closed_on=date(2026, 7, 2)
    )
    text = (tmp_path / "completed" / "2026-07-02-x.md").read_text(encoding="utf-8")
    assert "(none recorded)" in text
