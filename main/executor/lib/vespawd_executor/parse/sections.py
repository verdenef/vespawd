"""Split Master Prompt into H1/H2 sections (Executor Spec §4.1)."""

from __future__ import annotations

import re
from dataclasses import dataclass

H1_POS = re.compile(r"^#\s+POS\s+MASTER\s+PROMPT\s*$", re.MULTILINE | re.IGNORECASE)
H1_LEGACY = re.compile(r"^#\s+CURSOR\s+MASTER\s+PROMPT\s*$", re.MULTILINE | re.IGNORECASE)
H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

REQUIRED_H2_ORDER = (
    "PROJECT BRIEF",
    "PROJECT CONTEXT UPDATES",
    "CURRENT TASK",
    "BACKLOG ITEMS",
)

EXECUTOR_INSTRUCTIONS_ALIASES = frozenset({"EXECUTOR INSTRUCTIONS", "CURSOR INSTRUCTIONS"})


@dataclass(frozen=True)
class SectionMap:
    document_kind: str
    sections: dict[str, str]
    preamble: str


def _normalize_heading(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).upper()


def locate_h1(text: str) -> tuple[re.Match[str] | None, str]:
    pos_match = H1_POS.search(text)
    if pos_match:
        return pos_match, "pos"
    legacy_match = H1_LEGACY.search(text)
    if legacy_match:
        return legacy_match, "legacy"
    return None, ""


def split_sections(text: str) -> tuple[SectionMap | None, list[str]]:
    """Return section bodies keyed by normalized H2 title, or errors."""
    errors: list[str] = []
    h1_match, kind = locate_h1(text)
    if h1_match is None:
        errors.append("Missing H1: # POS MASTER PROMPT (or legacy # CURSOR MASTER PROMPT)")
        return None, errors

    preamble = text[: h1_match.start()]
    if preamble.strip():
        errors.append("Content before H1 is not allowed (Planner output contract §4.1)")

    body = text[h1_match.start() :]
    matches = list(H2_PATTERN.finditer(body))
    if not matches:
        errors.append("No H2 sections found after H1")
        return None, errors

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = _normalize_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip()

    return SectionMap(document_kind=kind, sections=sections, preamble=preamble), errors


def validate_section_order(sections: dict[str, str]) -> list[str]:
    """Validate required H2 sections appear in normative order (§4.1)."""
    errors: list[str] = []
    missing: list[str] = []

    found_titles = list(sections.keys())
    positions: dict[str, int] = {title: found_titles.index(title) for title in found_titles}

    last_index = -1
    for required in REQUIRED_H2_ORDER:
        if required not in positions:
            missing.append(required)
            continue
        if positions[required] < last_index:
            errors.append(f"Section out of order: {required}")
        last_index = positions[required]

    instruction_key = None
    for alias in EXECUTOR_INSTRUCTIONS_ALIASES:
        if alias in positions:
            instruction_key = alias
            break
    if instruction_key is None:
        missing.append("EXECUTOR INSTRUCTIONS")
    elif positions[instruction_key] < last_index:
        errors.append(f"Section out of order: {instruction_key}")

    errors.extend(f"Missing required section: {name}" for name in missing)
    return errors


def get_section(sections: dict[str, str], *names: str) -> str:
    for name in names:
        key = _normalize_heading(name)
        if key in sections:
            return sections[key]
    return ""
