"""Executor contract — vedaws_commands_run audit (§11.5)."""

from __future__ import annotations

import re

# Expected root CLI verbs per operation sequence (§4).
EXPECTED_COMMAND_ROOTS: dict[str, set[str]] = {
    "bootstrap": {"init", "workflow", "doctor", "state", "status"},
    "ingest_master_prompt": {"status", "state", "workflow"},
    "sync_status": {"status", "workflow", "state"},
    "pre_implement_check": {"doctor", "workflow"},
    "post_implement": {"run"},
    "post_phase_complete": {"tasks", "run", "state", "status", "workflow"},
    "pre_documenter": {"doctor", "software", "tasks", "status", "workflow", "state"},
}


def _roots(commands_run: list[str]) -> set[str]:
    roots: set[str] = set()
    for line in commands_run:
        tokens = line.split()
        for idx, token in enumerate(tokens):
            if token.endswith("vedaws") or token == "vedaws":
                if idx + 1 < len(tokens):
                    roots.add(tokens[idx + 1].lstrip("-"))
                break
            if token == "-m" and idx + 2 < len(tokens) and tokens[idx + 1] == "vedaws":
                roots.add(tokens[idx + 2])
                break
    return roots


def test_expected_audit_roots_defined() -> None:
    assert len(EXPECTED_COMMAND_ROOTS) == 7
    for op, roots in EXPECTED_COMMAND_ROOTS.items():
        assert roots, op


def test_audit_root_extractor() -> None:
    sample = ["python -m vedaws doctor --path /tmp/main"]
    assert "doctor" in _roots(sample)
