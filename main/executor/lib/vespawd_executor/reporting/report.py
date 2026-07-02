"""Structured Executor report (Executor Spec §10.7, lifecycle step 9 REPORT).

Tool-neutral (§14): no IDE-specific terminology. The report is a deterministic,
facts-only summary the Executor surfaces to the user after a phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_HANDOFF_READY_SIGNAL = "Submission handoff is ready for your documenter + rubric."


class NextAction(str, Enum):
    HUMAN_TEST = "human_test"
    PLANNER_FOLLOW_UP = "planner_follow_up"
    EXECUTOR_FIX = "executor_fix"
    RESOLVE_BLOCKERS = "resolve_blockers"


_NEXT_ACTION_TEXT = {
    NextAction.HUMAN_TEST: "Human test the changes, then send a Planner follow-up for the next phase.",
    NextAction.PLANNER_FOLLOW_UP: "Send a Planner follow-up for the next phase.",
    NextAction.EXECUTOR_FIX: "Request a small fix in this Executor chat.",
    NextAction.RESOLVE_BLOCKERS: "Resolve the listed blockers, then re-run the gate.",
}


@dataclass
class ExecutorReport:
    """§10.7 report fields."""

    ok: bool = True
    changed: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    run_commands: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    handoff_current: bool = False
    handoff_ready: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_action: NextAction = NextAction.HUMAN_TEST

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "changed": list(self.changed),
            "features": list(self.features),
            "run_commands": list(self.run_commands),
            "test_commands": list(self.test_commands),
            "handoff_current": self.handoff_current,
            "handoff_ready": self.handoff_ready,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "next_action": self.next_action.value,
        }

    def to_markdown(self) -> str:
        lines: list[str] = []

        lines.append("## What changed")
        lines.append("")
        if self.features:
            lines.extend(f"- {f}" for f in self.features)
        if self.changed:
            lines.extend(f"- `{c}`" for c in self.changed)
        if not self.features and not self.changed:
            lines.append("- (no changes recorded)")
        lines.append("")

        lines.append("## How to run and test")
        lines.append("")
        if self.run_commands or self.test_commands:
            lines.append("```text")
            lines.extend(self.run_commands)
            lines.extend(self.test_commands)
            lines.append("```")
        else:
            lines.append("- (no commands recorded)")
        lines.append("")

        lines.append("## Handoff")
        lines.append("")
        lines.append(f"- HANDOFF current: {'yes' if self.handoff_current else 'no'}")
        lines.append("")

        if self.blockers:
            lines.append("## Blockers")
            lines.append("")
            lines.extend(f"- {b}" for b in self.blockers)
            lines.append("")

        if self.warnings:
            lines.append("## Warnings")
            lines.append("")
            lines.extend(f"- {w}" for w in self.warnings)
            lines.append("")

        lines.append("## Next suggested action")
        lines.append("")
        lines.append(f"- {_NEXT_ACTION_TEXT[self.next_action]}")
        lines.append("")

        if self.handoff_ready:
            lines.append(f"> *{_HANDOFF_READY_SIGNAL}*")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def _pick_next_action(
    *,
    ok: bool,
    blockers: list[str],
    handoff_ready: bool,
    changed: list[str],
) -> NextAction:
    if blockers or not ok:
        return NextAction.RESOLVE_BLOCKERS
    if handoff_ready:
        return NextAction.PLANNER_FOLLOW_UP
    if changed:
        return NextAction.HUMAN_TEST
    return NextAction.EXECUTOR_FIX


def build_report(
    *,
    ok: bool = True,
    changed: list[str] | None = None,
    features: list[str] | None = None,
    run_commands: list[str] | None = None,
    test_commands: list[str] | None = None,
    handoff_current: bool = False,
    handoff_ready: bool = False,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    next_action: NextAction | None = None,
) -> ExecutorReport:
    """Build a §10.7 report. `next_action` is inferred when not supplied."""
    changed = list(changed or [])
    blockers = list(blockers or [])
    action = next_action or _pick_next_action(
        ok=ok, blockers=blockers, handoff_ready=handoff_ready, changed=changed
    )
    return ExecutorReport(
        ok=ok and not blockers,
        changed=changed,
        features=list(features or []),
        run_commands=list(run_commands or []),
        test_commands=list(test_commands or []),
        handoff_current=handoff_current,
        handoff_ready=handoff_ready,
        blockers=blockers,
        warnings=list(warnings or []),
        next_action=action,
    )
