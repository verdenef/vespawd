"""Vedaws CLI allowlist (Bridge Spec §7.1)."""

from __future__ import annotations

ALLOWED_ROOT_COMMANDS = frozenset(
    {
        "version",
        "init",
        "doctor",
        "status",
        "workflow",
        "run",
        "tasks",
        "state",
        "software",
    }
)

ALLOWED_WORKFLOW_SUBCOMMANDS = frozenset({"show", "activate"})
ALLOWED_TASKS_SUBCOMMANDS = frozenset({"complete", "fail", "show"})
ALLOWED_STATE_SUBCOMMANDS = frozenset({"transition", "history"})
ALLOWED_SOFTWARE_SUBCOMMANDS = frozenset({"artifacts", "status", "workflow"})


def validate_argv(argv: list[str]) -> bool:
    if not argv:
        return False
    root = argv[0]
    if root not in ALLOWED_ROOT_COMMANDS:
        return False
    if root == "workflow" and len(argv) > 1 and argv[1] not in ALLOWED_WORKFLOW_SUBCOMMANDS:
        return False
    if root == "tasks" and len(argv) > 1 and argv[1] not in ALLOWED_TASKS_SUBCOMMANDS:
        return False
    if root == "state" and len(argv) > 1 and argv[1] not in ALLOWED_STATE_SUBCOMMANDS:
        return False
    if root == "software" and len(argv) > 1 and argv[1] not in ALLOWED_SOFTWARE_SUBCOMMANDS:
        return False
    return True
