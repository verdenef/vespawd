"""Worker type categories."""

from __future__ import annotations

from enum import Enum


class WorkerType(str, Enum):
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str) -> WorkerType | None:
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return None
