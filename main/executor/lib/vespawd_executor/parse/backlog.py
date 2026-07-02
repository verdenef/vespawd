"""BACKLOG ITEMS parser (Executor Spec §4.5, Planner Spec §6)."""

from __future__ import annotations

import re

from vespawd_executor.parse.types import BacklogItemParsed

_STRUCTURED = re.compile(
    r"^\s*-\s*\[\s*\]\s*\*\*(.+?)\*\*\s*[—\-]\s*(.+?)(?:\s*_\((priority:\s*[^)]+)\)_)?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_SIMPLE = re.compile(r"^\s*-\s*\[\s*\]\s+(.+)$", re.MULTILINE)


def parse_backlog_items(body: str) -> list[BacklogItemParsed]:
    items: list[BacklogItemParsed] = []
    seen_titles: set[str] = set()

    for match in _STRUCTURED.finditer(body):
        title = match.group(1).strip()
        description = match.group(2).strip()
        priority = match.group(3).strip() if match.group(3) else None
        if priority and priority.lower().startswith("priority:"):
            priority = priority.split(":", 1)[1].strip()
        key = title.lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        items.append(
            BacklogItemParsed(
                title=title,
                description=description,
                priority=priority,
                raw_line=match.group(0).strip(),
            )
        )

    for match in _SIMPLE.finditer(body):
        line = match.group(0).strip()
        if _STRUCTURED.match(line):
            continue
        text = match.group(1).strip()
        title = text
        description = ""
        if " — " in text:
            title, description = text.split(" — ", 1)
        elif " - " in text:
            title, description = text.split(" - ", 1)
        key = title.lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        items.append(
            BacklogItemParsed(
                title=title.strip(),
                description=description.strip(),
                raw_line=line,
            )
        )

    return items
