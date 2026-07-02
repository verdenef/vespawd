"""PROJECT CONTEXT UPDATES parser tests (§4.3)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.context_updates import parse_context_updates
from vespawd_executor.parse.sections import get_section, split_sections

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_sample_context() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    body = get_section(section_map.sections, "PROJECT CONTEXT UPDATES")
    ctx = parse_context_updates(body)
    assert ctx.product_name == "CourseReg"
    assert ctx.mode == "sidecar"
    assert ctx.application_code == "main/src/"
    assert ctx.database == "MySQL"


def test_parse_name_alt_bullet() -> None:
    ctx = parse_context_updates("- **Name:** myapp\n")
    assert ctx.product_name == "myapp"
