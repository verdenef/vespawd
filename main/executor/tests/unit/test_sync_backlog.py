"""backlog.md writer tests (§4.5)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.backlog import parse_backlog_items
from vespawd_executor.parse.sections import get_section, split_sections
from vespawd_executor.sync.backlog import append_backlog_items

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")


def test_append_new_items(tmp_path: Path) -> None:
    path = tmp_path / "backlog.md"
    path.write_text("# Backlog\n\n## Items\n\n", encoding="utf-8")
    section_map, _ = split_sections(SAMPLE)
    items = parse_backlog_items(get_section(section_map.sections, "BACKLOG ITEMS"))
    count, _ = append_backlog_items(path, items)
    assert count == 2
    text = path.read_text(encoding="utf-8")
    assert "Architecture" in text
    assert "Submission documentation" in text


def test_skip_duplicate_items(tmp_path: Path) -> None:
    path = tmp_path / "backlog.md"
    path.write_text(
        "# Backlog\n\n## Items\n\n- [ ] **Architecture** — existing\n",
        encoding="utf-8",
    )
    section_map, _ = split_sections(SAMPLE)
    items = parse_backlog_items(get_section(section_map.sections, "BACKLOG ITEMS"))
    count, _ = append_backlog_items(path, items)
    assert count == 1
    text = path.read_text(encoding="utf-8")
    assert text.count("Architecture") == 1


def test_append_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "backlog.md"
    section_map, _ = split_sections(SAMPLE)
    items = parse_backlog_items(get_section(section_map.sections, "BACKLOG ITEMS"))
    append_backlog_items(path, items)
    first = path.read_text(encoding="utf-8")
    count, _ = append_backlog_items(path, items)
    assert count == 0
    assert path.read_text(encoding="utf-8") == first
