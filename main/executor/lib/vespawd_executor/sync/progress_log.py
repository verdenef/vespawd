"""Append implementation summary to current_task.md Progress Log (Executor Spec §8.3)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from vespawd_executor.sync.io import atomic_write

_PROGRESS_HEADER = "## Progress Log"
_TABLE_HEADER = "| Date | Update |\n|------|--------|"


def _summarize_changes(changed_paths: list[str], max_listed: int = 5) -> str:
    cleaned = [p.strip().replace("\\", "/") for p in changed_paths if p and p.strip()]
    if not cleaned:
        return "Implementation step (no files reported)"
    count = len(cleaned)
    listed = ", ".join(cleaned[:max_listed])
    if count > max_listed:
        listed += f", +{count - max_listed} more"
    noun = "file" if count == 1 else "files"
    return f"Implemented {count} {noun}: {listed}"


def _ensure_progress_section(text: str) -> str:
    if _PROGRESS_HEADER in text:
        return text
    suffix = "" if text.endswith("\n") else "\n"
    return f"{text}{suffix}\n{_PROGRESS_HEADER}\n\n{_TABLE_HEADER}\n"


def append_progress_entry(
    path: Path,
    changed_paths: list[str],
    *,
    logged_at: date | None = None,
    note: str | None = None,
) -> tuple[str, bool]:
    """Append a Progress Log row summarizing changed files (§8.3).

    Idempotent: an identical `| date | update |` row is not duplicated.
    Returns (path, appended).
    """
    stamp = (logged_at or date.today()).isoformat()
    update = note.strip() if note else _summarize_changes(changed_paths)
    row = f"| {stamp} | {update} |"

    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    existing = _ensure_progress_section(existing)

    # Idempotency: skip if this exact row already exists.
    if re.search(r"(?m)^" + re.escape(row) + r"\s*$", existing):
        atomic_write(path, existing)
        return str(path), False

    body = existing if existing.endswith("\n") else existing + "\n"
    body = body + row + "\n"
    atomic_write(path, body)
    return str(path), True
