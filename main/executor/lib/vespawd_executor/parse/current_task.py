"""CURRENT TASK section parser (Executor Spec §4.4, Planner Spec §5)."""

from __future__ import annotations

import re

from vespawd_executor.parse.types import CurrentTaskParsed

H3_PATTERN = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
STATUS_PATTERN = re.compile(r"^\s*Status:\s*(\S+)\s*$", re.MULTILINE | re.IGNORECASE)
CHECKBOX_PATTERN = re.compile(r"^\s*-\s*\[[ xX]\]\s+(.+)$", re.MULTILINE)


def _normalize_h3(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def parse_current_task(body: str) -> tuple[CurrentTaskParsed | None, list[str]]:
    errors: list[str] = []
    if not body.strip():
        errors.append("CURRENT TASK section is empty")
        return None, errors

    status_match = STATUS_PATTERN.search(body)
    status = status_match.group(1).strip() if status_match else ""
    if not status:
        errors.append("CURRENT TASK missing Status line")
    elif status.lower() != "in_progress":
        errors.append(f"CURRENT TASK Status should be in_progress (got {status!r})")

    h3_matches = list(H3_PATTERN.finditer(body))
    subsections: dict[str, str] = {}
    for index, match in enumerate(h3_matches):
        title = _normalize_h3(match.group(1))
        start = match.end()
        end = h3_matches[index + 1].start() if index + 1 < len(h3_matches) else len(body)
        subsections[title] = body[start:end].strip()

    goal = subsections.get("goal", "").strip()
    if not goal:
        errors.append("CURRENT TASK missing Goal (### Goal)")

    acceptance = subsections.get("acceptance criteria", "").strip()
    acceptance_items = tuple(m.group(1).strip() for m in CHECKBOX_PATTERN.finditer(acceptance))
    if not acceptance:
        errors.append("CURRENT TASK missing Acceptance criteria (### Acceptance criteria)")
    elif not acceptance_items:
        errors.append("CURRENT TASK Acceptance criteria must include at least one checkbox item")

    if errors:
        return None, errors

    return (
        CurrentTaskParsed(
            status=status,
            goal=goal,
            constraints=subsections.get("constraints", "").strip(),
            acceptance_criteria=acceptance,
            notes=subsections.get("notes", "").strip(),
            acceptance_items=acceptance_items,
        ),
        [],
    )
