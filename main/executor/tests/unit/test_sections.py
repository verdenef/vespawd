"""Section splitter tests (§4.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.sections import split_sections, validate_section_order


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_split_sample_sections() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, errors = split_sections(text)
    assert errors == []
    assert section_map is not None
    assert section_map.document_kind == "pos"
    assert "PROJECT BRIEF" in section_map.sections
    assert "CURRENT TASK" in section_map.sections
    assert "EXECUTOR INSTRUCTIONS" in section_map.sections


def test_split_legacy_h1() -> None:
    text = (FIXTURES / "legacy_master_prompt.md").read_text(encoding="utf-8")
    section_map, errors = split_sections(text)
    assert errors == []
    assert section_map is not None
    assert section_map.document_kind == "legacy"
    assert "CURSOR INSTRUCTIONS" in section_map.sections


def test_missing_h1() -> None:
    section_map, errors = split_sections("## PROJECT BRIEF\n\nHi\n")
    assert section_map is None
    assert any("Missing H1" in e for e in errors)


def test_content_before_h1_error() -> None:
    text = "Preamble text\n\n# POS MASTER PROMPT\n\n## PROJECT BRIEF\n\nx\n"
    section_map, errors = split_sections(text)
    assert section_map is not None
    assert any("before H1" in e for e in errors)


def test_validate_section_order_ok() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    section_map, _ = split_sections(text)
    assert section_map is not None
    assert validate_section_order(section_map.sections) == []


def test_validate_missing_section() -> None:
    errors = validate_section_order({"PROJECT BRIEF": "x"})
    assert any("PROJECT CONTEXT UPDATES" in e for e in errors)
