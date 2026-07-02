"""Progress Log writer unit tests (§8.3)."""

from __future__ import annotations

from datetime import date

from vespawd_executor.sync.progress_log import append_progress_entry


def test_appends_entry_and_creates_section(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n\n## Goal\n\nBuild service\n", encoding="utf-8")
    _, appended = append_progress_entry(
        path, ["main/src/a.py", "main/src/b.py"], logged_at=date(2026, 7, 2)
    )
    assert appended
    text = path.read_text(encoding="utf-8")
    assert "## Progress Log" in text
    assert "| 2026-07-02 | Implemented 2 files: main/src/a.py, main/src/b.py |" in text


def test_idempotent_same_row(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n", encoding="utf-8")
    changed = ["main/src/a.py"]
    _, first = append_progress_entry(path, changed, logged_at=date(2026, 7, 2))
    _, second = append_progress_entry(path, changed, logged_at=date(2026, 7, 2))
    assert first is True
    assert second is False
    text = path.read_text(encoding="utf-8")
    assert text.count("Implemented 1 file: main/src/a.py") == 1


def test_single_file_singular(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n", encoding="utf-8")
    append_progress_entry(path, ["main/src/only.py"], logged_at=date(2026, 7, 2))
    text = path.read_text(encoding="utf-8")
    assert "Implemented 1 file:" in text


def test_truncates_long_list(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n", encoding="utf-8")
    changed = [f"main/src/f{i}.py" for i in range(8)]
    append_progress_entry(path, changed, logged_at=date(2026, 7, 2))
    text = path.read_text(encoding="utf-8")
    assert "+3 more" in text


def test_custom_note(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n", encoding="utf-8")
    append_progress_entry(path, [], logged_at=date(2026, 7, 2), note="Refactored auth module")
    text = path.read_text(encoding="utf-8")
    assert "| 2026-07-02 | Refactored auth module |" in text


def test_empty_changes_note(tmp_path) -> None:
    path = tmp_path / "current_task.md"
    path.write_text("# Current Task\n", encoding="utf-8")
    _, appended = append_progress_entry(path, [], logged_at=date(2026, 7, 2))
    assert appended
    text = path.read_text(encoding="utf-8")
    assert "no files reported" in text
