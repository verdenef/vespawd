"""Master Prompt trigger recognition (Executor Spec §3.1)."""

from __future__ import annotations

import re

from vespawd_executor.api.types import TriggerKind

_POS_H1 = re.compile(r"^#\s+POS\s+MASTER\s+PROMPT\s*$", re.MULTILINE | re.IGNORECASE)
_LEGACY_H1 = re.compile(r"^#\s+CURSOR\s+MASTER\s+PROMPT\s*$", re.MULTILINE | re.IGNORECASE)
_EXECUTE_PHRASE = re.compile(
    r"\bexecute\s+master\s+prompt\b",
    re.IGNORECASE,
)


def detect_trigger(text: str) -> TriggerKind:
    """Return how the user invoked the Executor for this message body."""
    if not text or not text.strip():
        return TriggerKind.NONE
    if _POS_H1.search(text):
        return TriggerKind.POS_MASTER_PROMPT
    if _LEGACY_H1.search(text):
        return TriggerKind.LEGACY_CURSOR_MASTER_PROMPT
    if _EXECUTE_PHRASE.search(text):
        return TriggerKind.EXPLICIT_EXECUTE
    return TriggerKind.NONE


def is_master_prompt(text: str) -> bool:
    return detect_trigger(text) != TriggerKind.NONE
