"""Merge PROJECT CONTEXT UPDATES into project_context.md (§4.3, §5.2)."""

from __future__ import annotations

import re
from pathlib import Path

from vespawd_executor.parse.types import ContextUpdatesParsed
from vespawd_executor.sync.io import atomic_write

_NAME_RE = re.compile(r"(\*\*Name:\*\*\s*)(\S+)", re.MULTILINE)


def _upsert_table_field(text: str, field: str, value: str) -> str:
    pattern = re.compile(
        rf"^(\|\s*{re.escape(field)}\s*\|\s*)([^|]*?)(\s*\|)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return text
    current = match.group(2).strip()
    new_value = value.strip()
    if current == new_value:
        return text
    return pattern.sub(rf"\1{new_value}\3", text, count=1)


_STRUCTURED_BULLET_KEYS = frozenset(
    {
        "mode",
        "pos folder",
        "application code",
        "product name",
        "database",
        "name",
    }
)


def _structured_bullet_key(bullet: str) -> str | None:
    match = re.match(r"^\s*[-*]\s*\*\*(.+?):\*\*", bullet.strip(), re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip().lower()


def _append_agent_note(text: str, bullet: str) -> str:
    normalized = bullet.strip()
    if normalized in text:
        return text
    marker = "## Agent Notes"
    if marker not in text:
        return text.rstrip() + f"\n\n{marker}\n\n{bullet.strip()}\n"
    parts = text.split(marker, 1)
    tail = parts[1]
    return parts[0] + marker + tail.rstrip() + f"\n{bullet.strip()}\n"


def _default_context(updates: ContextUpdatesParsed) -> str:
    name = updates.product_name or "TBD"
    mode = updates.mode or "sidecar"
    pos_folder = updates.pos_folder or "paws022/"
    app_code = updates.application_code or "main/src/"
    database = updates.database or "_TBD_"
    return f"""# Project Context (POS Memory)

> Single source of truth for this repository.

## Product

- **Name:** {name}
- **Summary:** _TBD_

## Tech Stack

| Area | Choice |
|------|--------|
| Language(s) | _TBD_ |
| Framework | _TBD_ |
| Database | {database} |
| Auth | _TBD_ |
| Deployment | _TBD_ |

## Layout

| Field | Value |
|-------|--------|
| Mode | {mode} |
| POS folder (sidecar) | {pos_folder} |
| Application code | `{app_code}` |

## Agent Notes

- _Add domain vocabulary and hard rules here._
"""


def merge_project_context(path: Path, updates: ContextUpdatesParsed) -> tuple[str, list[str]]:
    """
    Merge parsed context updates into existing project_context.md.

    Preserves prior facts unless an update field explicitly supersedes (Planner §7.3).
    Returns (relative_path_marker, warnings) — path is for caller tracking.
    """
    warnings: list[str] = []
    if not updates.raw.strip() and not any(
        [updates.product_name, updates.mode, updates.application_code, updates.database]
    ):
        warnings.append("No PROJECT CONTEXT UPDATES to merge")
        if path.is_file():
            return str(path), warnings
        content = _default_context(updates)
        atomic_write(path, content)
        return str(path), warnings

    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = _default_context(updates)
        warnings.append("Created new project_context.md")

    if updates.product_name:
        if _NAME_RE.search(text):
            text = _NAME_RE.sub(rf"\1{updates.product_name}", text, count=1)
        else:
            text = _append_agent_note(text, f"- **Name:** {updates.product_name}")

    if updates.mode:
        text = _upsert_table_field(text, "Mode", updates.mode)

    if updates.pos_folder:
        text = _upsert_table_field(text, "POS folder (sidecar)", updates.pos_folder)

    if updates.application_code:
        value = updates.application_code.strip("`")
        text = _upsert_table_field(text, "Application code", f"`{value}`")

    if updates.database:
        text = _upsert_table_field(text, "Database", updates.database)

    for bullet in updates.bullets:
        key = _structured_bullet_key(bullet)
        if key and key in _STRUCTURED_BULLET_KEYS:
            continue
        text = _append_agent_note(text, bullet)

    atomic_write(path, text if text.endswith("\n") else text + "\n")
    return str(path), warnings
