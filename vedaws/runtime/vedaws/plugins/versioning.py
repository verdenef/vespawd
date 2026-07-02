"""Version constraint evaluation."""

from __future__ import annotations

import re
import sys

_CONSTRAINT_RE = re.compile(r"^(>=|<=|==|>|<|~=)\s*(.+)$")


def parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for segment in version.strip().split("."):
        match = re.match(r"(\d+)", segment)
        parts.append(int(match.group(1)) if match else 0)
    return tuple(parts) if parts else (0,)


def satisfies_constraint(version: str, constraint: str) -> bool:
    constraint = constraint.strip()
    if not constraint:
        return True
    match = _CONSTRAINT_RE.match(constraint)
    if not match:
        return version == constraint
    operator, required = match.group(1), match.group(2)
    left = parse_version(version)
    right = parse_version(required)
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == "==":
        return left == right
    if operator == "~=":
        return left[:2] == right[:2] and left >= right
    return False


def python_satisfies(constraint: str) -> bool:
    current = ".".join(str(part) for part in sys.version_info[:3])
    return satisfies_constraint(current, constraint)
