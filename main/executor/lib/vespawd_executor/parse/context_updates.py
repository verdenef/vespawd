"""PROJECT CONTEXT UPDATES parser (Executor Spec §4.3, Planner Spec §7)."""

from __future__ import annotations

import re

from vespawd_executor.parse.types import ContextUpdatesParsed

_BULLET_KV = re.compile(
    r"^\s*[-*]\s*\*\*(.+?):\*\*\s*(.+?)\s*$",
    re.MULTILINE,
)
_NAME_ALT = re.compile(r"^\s*[-*]\s*\*\*Name:\*\*\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def _clean_value(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_context_updates(body: str) -> ContextUpdatesParsed:
    raw = body.strip()
    bullets: list[str] = []
    fields: dict[str, str] = {}

    for match in _BULLET_KV.finditer(raw):
        key = match.group(1).strip().lower()
        value = _clean_value(match.group(2))
        bullets.append(match.group(0).strip())
        fields[key] = value

    name_match = _NAME_ALT.search(raw)
    if name_match and "product name" not in fields:
        fields["product name"] = _clean_value(name_match.group(1))

    return ContextUpdatesParsed(
        raw=raw,
        product_name=fields.get("product name"),
        mode=fields.get("mode"),
        application_code=fields.get("application code"),
        pos_folder=fields.get("pos folder"),
        database=fields.get("database"),
        bullets=tuple(bullets),
    )
