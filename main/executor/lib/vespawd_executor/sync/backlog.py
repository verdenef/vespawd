"""Append BACKLOG ITEMS to backlog.md (§4.5, §5.2)."""

from __future__ import annotations

import re

from vespawd_executor.parse.types import BacklogItemParsed
from vespawd_executor.sync.io import atomic_write

_TITLE_RE = re.compile(r"\*\*(.+?)\*\*", re.IGNORECASE)
_ITEMS_HEADER = "## Items"


def _existing_titles(text: str) -> set[str]:
    titles: set[str] = set()
    for match in _TITLE_RE.finditer(text):
        titles.add(match.group(1).strip().lower())
    for line in text.splitlines():
        if line.strip().startswith("- [ ]") and "**" not in line:
            plain = line.split("- [ ]", 1)[-1].strip().split("—")[0].split(" - ")[0].strip()
            if plain:
                titles.add(plain.lower())
    return titles


def _format_item(item: BacklogItemParsed) -> str:
    if item.raw_line:
        return item.raw_line.strip()
    priority = f" _(priority: {item.priority})_" if item.priority else ""
    description = f" — {item.description}" if item.description else ""
    return f"- [ ] **{item.title}**{description}{priority}"


def _default_backlog() -> str:
    return """# Backlog (POS Scheduler)

> **Per-project** queue.

## Items

"""


def append_backlog_items(path, items: list[BacklogItemParsed]) -> tuple[int, str]:
    """Append backlog items skipping duplicates. Returns (count appended, path)."""
    if not items:
        if path.is_file():
            return 0, str(path)
        atomic_write(path, _default_backlog())
        return 0, str(path)

    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = _default_backlog()

    existing = _existing_titles(text)
    new_lines: list[str] = []
    for item in items:
        key = item.title.strip().lower()
        if key in existing:
            continue
        existing.add(key)
        new_lines.append(_format_item(item))

    if not new_lines:
        return 0, str(path)

    if _ITEMS_HEADER in text:
        text = text.rstrip() + "\n" + "\n".join(new_lines) + "\n"
    else:
        text = text.rstrip() + f"\n\n{_ITEMS_HEADER}\n\n" + "\n".join(new_lines) + "\n"

    atomic_write(path, text)
    return len(new_lines), str(path)
