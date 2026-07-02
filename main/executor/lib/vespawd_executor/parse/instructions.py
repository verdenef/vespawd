"""EXECUTOR INSTRUCTIONS parser (Executor Spec §4.6, Planner Spec §8)."""

from __future__ import annotations

import re

_NUMBERED = re.compile(r"^\s*\d+\.\s+(.+)$", re.MULTILINE)
_BULLET = re.compile(r"^\s*[-*]\s+(.+)$", re.MULTILINE)


def parse_executor_instructions(body: str) -> list[str]:
    numbered = [m.group(1).strip() for m in _NUMBERED.finditer(body)]
    if numbered:
        return numbered

    bullets = [m.group(1).strip() for m in _BULLET.finditer(body)]
    return bullets


def detect_instruction_conflicts(
    instructions: list[str],
    acceptance_items: tuple[str, ...],
) -> list[str]:
    """
    §4.6: acceptance criteria win on scope; surface obvious contradictions as notes.
    Conservative heuristic only — full conflict resolution is Executor judgment.
    """
    conflicts: list[str] = []
    instruction_text = " ".join(instructions).lower()
    for item in acceptance_items:
        item_lower = item.lower()
        if "implement" in item_lower and "do not implement" in instruction_text:
            conflicts.append(
                "EXECUTOR INSTRUCTIONS may contradict acceptance criteria on implementation scope"
            )
            break
    return conflicts
