"""Append notes to current_task.md ## Notes (Executor Spec §11.5, §12.5)."""

from __future__ import annotations

import re
from pathlib import Path

from vespawd_executor.sync.io import atomic_write

_NOTES_HEADER = "## Notes"
_PROGRESS_HEADER = "## Progress Log"


def _ensure_notes_section(text: str) -> str:
    if _NOTES_HEADER in text:
        return text
    if _PROGRESS_HEADER in text:
        return text.replace(_PROGRESS_HEADER, f"{_NOTES_HEADER}\n\n-\n\n{_PROGRESS_HEADER}", 1)
    suffix = "" if text.endswith("\n") else "\n"
    return f"{text}{suffix}\n{_NOTES_HEADER}\n\n-\n"


def _notes_bounds(text: str) -> tuple[int, int]:
    start = text.find(_NOTES_HEADER) + len(_NOTES_HEADER)
    tail = text[start:]
    nxt = re.search(r"(?m)^## ", tail)
    end = start + nxt.start() if nxt else len(text)
    return start, end


def append_task_note(path: Path, note: str, *, prefix: str = "Executor note") -> tuple[str, bool]:
    """Append a bullet to the current_task.md ## Notes section (§11.5, §12.5).

    Idempotent: an identical bullet is not duplicated. Returns (path, appended).
    """
    clean = note.strip()
    if not clean:
        return str(path), False
    bullet = f"- {prefix}: {clean}" if prefix else f"- {clean}"

    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else "# Current Task\n"
    text = _ensure_notes_section(text)

    if re.search(r"(?m)^" + re.escape(bullet) + r"\s*$", text):
        atomic_write(path, text)
        return str(path), False

    start, end = _notes_bounds(text)
    body = text[start:end]
    # Drop a lone placeholder dash before appending real content.
    stripped_lines = [ln for ln in body.splitlines() if ln.strip() not in {"", "-"}]
    stripped_lines.append(bullet)
    new_body = "\n\n" + "\n".join(stripped_lines) + "\n\n"
    updated = text[:start] + new_body + text[end:]
    atomic_write(path, updated)
    return str(path), True
