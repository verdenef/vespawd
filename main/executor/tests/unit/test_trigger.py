"""Trigger recognition tests (§3.1)."""

from __future__ import annotations

from vespawd_executor.api.types import TriggerKind
from vespawd_executor.startup.trigger import detect_trigger, is_master_prompt


def test_pos_master_prompt_h1() -> None:
    text = "# POS MASTER PROMPT\n\n## PROJECT BRIEF\n"
    assert detect_trigger(text) == TriggerKind.POS_MASTER_PROMPT
    assert is_master_prompt(text)


def test_legacy_cursor_h1() -> None:
    text = "# CURSOR MASTER PROMPT\n\n## PROJECT BRIEF\n"
    assert detect_trigger(text) == TriggerKind.LEGACY_CURSOR_MASTER_PROMPT


def test_explicit_execute_phrase() -> None:
    text = "Please execute master prompt with the following:\n# POS MASTER PROMPT\n"
    assert detect_trigger(text) == TriggerKind.POS_MASTER_PROMPT


def test_natural_language_not_trigger() -> None:
    assert detect_trigger("fix the login bug") == TriggerKind.NONE
    assert not is_master_prompt("fix the login bug")
