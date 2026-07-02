"""EXECUTOR INSTRUCTIONS parser tests (§4.6)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.instructions import (
    detect_instruction_conflicts,
    parse_executor_instructions,
)
from vespawd_executor.parse.sections import get_section, split_sections

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_numbered_instructions() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    body = get_section(section_map.sections, "EXECUTOR INSTRUCTIONS")
    steps = parse_executor_instructions(body)
    assert len(steps) == 3
    assert "project_context" in steps[0]


def test_parse_legacy_cursor_instructions() -> None:
    text = (FIXTURES / "legacy_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    body = get_section(section_map.sections, "CURSOR INSTRUCTIONS")
    steps = parse_executor_instructions(body)
    assert len(steps) == 2


def test_detect_conflicts_empty_by_default() -> None:
    assert detect_instruction_conflicts(["Merge context"], ("Implement feature",)) == []
