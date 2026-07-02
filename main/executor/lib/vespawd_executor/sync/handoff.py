"""Seed and refresh HANDOFF_FOR_DOCUMENTER.md (§5.3 step 4, §5.4 step 4, §13)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from vespawd_executor.parse.types import (
    ContextUpdatesParsed,
    CurrentTaskParsed,
    ParsedMasterPrompt,
)
from vespawd_executor.sync.io import atomic_write

_WHAT_BUILT_HEADER = "## What was built"
_FOOTER_RE = re.compile(r"^_Generated:.*_$", re.MULTILINE)


def _default_handoff() -> str:
    return """# Handoff for documenter (POS)

> **Executor maintains this automatically**.

## Project

- **Name:**
- **Course / assignment:**
- **Team members:**

## What was built

## How to run

```text

```

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | |
| Framework | |
| Database | |

## Features implemented

- [ ]

## Features not implemented

-

## Testing / demo

1.

## Known limitations

-

## Rubric checklist

- [ ]

---

_Generated: — | Repo: —_
"""


def _upsert_footer(text: str, repo_path: str, timestamp: str) -> str:
    footer = f"_Generated: {timestamp} | Repo: {repo_path}_"
    match = _FOOTER_RE.search(text)
    if match:
        text = text[: match.start()] + footer + text[match.end() :]
    else:
        text = text.rstrip() + f"\n\n---\n\n{footer}\n"

    if "Last updated:" not in text:
        text = text.replace(
            "---\n\n" + footer,
            f"Last updated: {timestamp}\n\n---\n\n{footer}",
            1,
        )
    return text


def _ensure_project_name(text: str, name: str) -> str:
    pattern = re.compile(r"- \*\*Name:\*\*[^\S\n]*[^\n]*", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda _m: f"- **Name:** {name}", text, count=1)
    if "## Project" in text:
        return text.replace("## Project", f"## Project\n\n- **Name:** {name}", 1)
    return f"## Project\n\n- **Name:** {name}\n\n" + text


def _upsert_database_row(text: str, database: str | None) -> str:
    if not database:
        return text
    pattern = re.compile(r"^(\|\s*Database\s*\|\s*)([^|]*)(\|\s*)$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(rf"\1{database}\3", text, count=1)
    return text


def _seed_what_built(text: str, goal: str, brief: str) -> str:
    if _WHAT_BUILT_HEADER not in text:
        return text
    parts = text.split(_WHAT_BUILT_HEADER, 1)
    body, rest = parts[1], parts[0]
    section_end = re.search(r"(?m)^## ", body)
    section_body = body[: section_end.start()] if section_end else body
    if section_body.strip():
        return text

    bullets = [f"- Phase goal: {goal.strip()}"]
    brief_line = brief.strip().splitlines()[0] if brief.strip() else ""
    if brief_line and brief_line not in goal:
        bullets.append(f"- Context: {brief_line}")
    insertion = "\n" + "\n".join(bullets) + "\n"
    if section_end:
        new_body = insertion + body[section_end.start() :]
    else:
        new_body = insertion
    return rest + _WHAT_BUILT_HEADER + new_body


def seed_handoff(
    path,
    parsed: ParsedMasterPrompt,
    *,
    repo_path: str,
    timestamp: datetime | None = None,
) -> tuple[str, list[str]]:
    """
    Seed HANDOFF with project name, stack hints, and phase goal (§13.1 ingest trigger).

    Preserves existing section content; only fills empty sections and updates metadata.
    """
    warnings: list[str] = []
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = _default_handoff()
        warnings.append("Created new HANDOFF_FOR_DOCUMENTER.md")

    ctx: ContextUpdatesParsed = parsed.project_context
    if ctx.product_name:
        text = _ensure_project_name(text, ctx.product_name)

    text = _upsert_database_row(text, ctx.database)
    text = _seed_what_built(text, parsed.current_task.goal, parsed.project_brief)
    text = _upsert_footer(text, repo_path, ts)

    atomic_write(path, text if text.endswith("\n") else text + "\n")
    return str(path), warnings


# --- §13 full refresh (§5.4 step 4, §13.1 "task/phase completes") -----------------

_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s*(.+?)\s*$")
_UNCHECKED_RE = re.compile(r"^\s*-\s*\[\s\]\s*(.+?)\s*$")


@dataclass
class HandoffFacts:
    """Factual inputs for a HANDOFF refresh (§13.2). Facts only — no invented content."""

    project_name: str | None = None
    database: str | None = None
    language: str | None = None
    framework: str | None = None
    what_built: list[str] = field(default_factory=list)
    features_done: list[str] = field(default_factory=list)
    features_pending: list[str] = field(default_factory=list)
    testing_steps: list[str] = field(default_factory=list)
    run_commands: list[str] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)


def handoff_facts_from_task(
    task: CurrentTaskParsed,
    context: ContextUpdatesParsed,
) -> HandoffFacts:
    """Derive facts from CURRENT TASK + project context (§13.3). No invention."""
    done: list[str] = []
    pending: list[str] = []
    for line in task.acceptance_criteria.splitlines():
        checked = _CHECKED_RE.match(line)
        unchecked = _UNCHECKED_RE.match(line)
        if checked:
            done.append(checked.group(1).strip())
        elif unchecked:
            pending.append(unchecked.group(1).strip())

    return HandoffFacts(
        project_name=context.product_name,
        database=context.database,
        features_done=done,
        features_pending=pending,
    )


def _section_bounds(text: str, header: str) -> tuple[int, int] | None:
    idx = text.find(header)
    if idx == -1:
        return None
    body_start = idx + len(header)
    tail = text[body_start:]
    nxt = re.search(r"(?m)^(## |---\s*$)", tail)
    body_end = body_start + nxt.start() if nxt else len(text)
    return body_start, body_end


_PLACEHOLDER_LINES = {"", "-", "- [ ]", "1.", "```text", "```"}


def _is_empty_section(body: str) -> bool:
    for line in body.strip().splitlines():
        if line.strip() not in _PLACEHOLDER_LINES:
            return False
    return True


def _fill_section(text: str, header: str, lines: list[str]) -> str:
    """Fill a section body only if it is empty/placeholder (facts-only, idempotent)."""
    if not lines:
        return text
    bounds = _section_bounds(text, header)
    if bounds is None:
        return text
    start, end = bounds
    body = text[start:end]
    if not _is_empty_section(body):
        return text
    filled = "\n\n" + "\n".join(lines) + "\n\n"
    return text[:start] + filled + text[end:]


def _fill_code_section(text: str, header: str, commands: list[str]) -> str:
    if not commands:
        return text
    bounds = _section_bounds(text, header)
    if bounds is None:
        return text
    start, end = bounds
    body = text[start:end]
    if not _is_empty_section(body):
        return text
    block = "\n\n```text\n" + "\n".join(commands) + "\n```\n\n"
    return text[:start] + block + text[end:]


def _upsert_stack_row(text: str, label: str, value: str | None) -> str:
    if not value:
        return text
    pattern = re.compile(rf"^(\|\s*{re.escape(label)}\s*\|\s*)([^|]*)(\|\s*)$", re.MULTILINE)
    match = pattern.search(text)
    if match and not match.group(2).strip():
        return pattern.sub(rf"\g<1>{value} \g<3>", text, count=1)
    return text


def refresh_handoff(
    path,
    facts: HandoffFacts,
    *,
    repo_path: str,
    timestamp: datetime | None = None,
) -> tuple[str, list[str]]:
    """
    Full HANDOFF refresh after implementation/completion (§5.4 step 4, §13).

    Facts-only: fills empty §13.2 sections from `facts`, preserves existing content,
    updates footer. Idempotent — re-running with the same facts is a no-op.
    """
    warnings: list[str] = []
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = _default_handoff()
        warnings.append("Created new HANDOFF_FOR_DOCUMENTER.md")

    if facts.project_name:
        text = _ensure_project_name(text, facts.project_name)

    text = _upsert_stack_row(text, "Language", facts.language)
    text = _upsert_stack_row(text, "Framework", facts.framework)
    text = _upsert_stack_row(text, "Database", facts.database)

    text = _fill_section(text, _WHAT_BUILT_HEADER, [f"- {b}" for b in facts.what_built])
    text = _fill_section(
        text, "## Features implemented", [f"- [x] {f}" for f in facts.features_done]
    )
    text = _fill_section(
        text, "## Features not implemented", [f"- {f}" for f in facts.features_pending]
    )
    text = _fill_section(
        text,
        "## Testing / demo",
        [f"{i}. {s}" for i, s in enumerate(facts.testing_steps, start=1)],
    )
    text = _fill_section(
        text, "## Known limitations", [f"- {lim}" for lim in facts.known_limitations]
    )
    text = _fill_code_section(text, "## How to run", facts.run_commands)

    text = _upsert_footer(text, repo_path, ts)

    atomic_write(path, text if text.endswith("\n") else text + "\n")
    return str(path), warnings
