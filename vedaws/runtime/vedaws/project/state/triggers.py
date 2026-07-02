"""Authorized transition cause categories."""

from __future__ import annotations

from enum import Enum


class TransitionTrigger(str, Enum):
    HUMAN_DECISION = "human_decision"
    TASK_OUTCOME = "task_outcome"
    AUTOMATION = "automation"
    WORKFLOW_RULE = "workflow_rule"
    SYSTEM = "system"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str) -> TransitionTrigger | None:
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return None
