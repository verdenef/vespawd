"""BACKLOG ITEMS parser tests (§4.5)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.backlog import parse_backlog_items
from vespawd_executor.parse.sections import get_section, split_sections

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_structured_backlog() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    body = get_section(section_map.sections, "BACKLOG ITEMS")
    items = parse_backlog_items(body)
    assert len(items) == 2
    assert items[0].title == "Architecture"
    assert items[0].priority == "high"
    assert items[1].title == "Submission documentation"


def test_parse_simple_backlog() -> None:
    items = parse_backlog_items("- [ ] Simple item — do later\n")
    assert len(items) == 1
    assert items[0].title == "Simple item"


def test_skip_duplicate_titles() -> None:
    body = "- [ ] **Architecture** — first\n- [ ] **Architecture** — duplicate\n"
    items = parse_backlog_items(body)
    assert len(items) == 1
