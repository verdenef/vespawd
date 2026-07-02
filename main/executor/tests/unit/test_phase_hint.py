"""Phase hint extraction tests."""

from __future__ import annotations

from vespawd_executor.parse.phase_hint import extract_phase_hint


def test_vedaws_phase_line() -> None:
    assert extract_phase_hint("- Vedaws phase: software.implement\n") == "implement"


def test_software_id_in_notes() -> None:
    assert extract_phase_hint("software.architecture") == "architecture"


def test_keyword_in_notes() -> None:
    assert extract_phase_hint("Focus on handoff package") == "handoff"


def test_goal_fallback() -> None:
    assert extract_phase_hint("", "Define API schema contracts") == "api-design"


def test_none_when_absent() -> None:
    assert extract_phase_hint("No phase here") is None
