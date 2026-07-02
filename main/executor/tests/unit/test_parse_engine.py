"""Full parse engine tests (§4.7)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse import parse_master_prompt, to_ingest_payload

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_sample_ok() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    result = parse_master_prompt(text)
    assert result.ok, result.errors
    assert result.parsed is not None
    assert result.parsed.phase_hint == "scope"
    assert result.parsed.current_task.goal
    assert len(result.parsed.backlog_items) == 2


def test_parse_legacy_ok() -> None:
    text = (FIXTURES / "legacy_master_prompt.md").read_text(encoding="utf-8")
    result = parse_master_prompt(text)
    assert result.ok, result.errors
    assert result.parsed is not None
    assert result.parsed.phase_hint == "implement"


def test_parse_missing_sections() -> None:
    text = "# POS MASTER PROMPT\n\n## PROJECT BRIEF\n\nOnly brief.\n"
    result = parse_master_prompt(text)
    assert not result.ok
    assert result.errors
    assert result.parsed is None


def test_parse_not_master_prompt() -> None:
    result = parse_master_prompt("fix the login bug")
    assert not result.ok
    assert any("not a recognized" in e for e in result.errors)


def test_to_ingest_payload_shape() -> None:
    text = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
    result = parse_master_prompt(text)
    assert result.ok and result.parsed
    payload = to_ingest_payload(result.parsed)
    assert payload["current_task"]["goal"]
    assert payload["phase_hint"] == "scope"
    assert payload["project_context"]["product_name"] == "CourseReg"
