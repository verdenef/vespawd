"""PAWS synchronization result types (Executor Spec §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PawsSyncResult:
    ok: bool = True
    files_written: list[str] = field(default_factory=list)
    backlog_appended: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "files_written": list(self.files_written),
            "backlog_appended": self.backlog_appended,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
