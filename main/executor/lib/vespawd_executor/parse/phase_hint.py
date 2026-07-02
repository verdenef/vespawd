"""Extract Vedaws phase hint from CURRENT TASK Notes (Planner Spec §5.2)."""

from __future__ import annotations

import re

_VEDAWS_PHASE = re.compile(
    r"(?:vedaws\s+phase|phase(?:\s+id)?)\s*:\s*(?:software\.)?([a-z0-9-]+)",
    re.IGNORECASE,
)
_SOFTWARE_ID = re.compile(r"\bsoftware\.([a-z0-9-]+)\b", re.IGNORECASE)
_CANONICAL_PHASES = (
    ("api-design", ("api-design", "api", "schema", "contracts")),
    ("architecture", ("architecture", "components", "adr")),
    ("scope", ("scope", "requirements", "mvp")),
    ("implement", ("implement", "feature", "build")),
    ("test", ("test", "verify", "demo")),
    ("review", ("review", "lint", "fix pass")),
    ("handoff", ("handoff", "submission package")),
)


def _keyword_phase(text: str) -> str | None:
    lowered = text.lower()
    for phase_id, keywords in _CANONICAL_PHASES:
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                return phase_id
    return None


def extract_phase_hint(notes: str, goal: str = "") -> str | None:
    combined = f"{notes}\n{goal}"
    vedaws = _VEDAWS_PHASE.search(combined)
    if vedaws:
        return vedaws.group(1).lower()

    software = _SOFTWARE_ID.search(combined)
    if software:
        return software.group(1).lower()

    return _keyword_phase(notes) or _keyword_phase(goal)
