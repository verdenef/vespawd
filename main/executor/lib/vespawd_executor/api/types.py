"""Public Executor API types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerKind(str, Enum):
    NONE = "none"
    POS_MASTER_PROMPT = "pos_master_prompt"
    LEGACY_CURSOR_MASTER_PROMPT = "legacy_cursor_master_prompt"
    EXPLICIT_EXECUTE = "explicit_execute"


@dataclass(frozen=True)
class SessionOptions:
    """Per-run session flags passed to Bridge via BridgeContext."""

    skip_design: bool = False
    design_later: bool = False
    force_phase: str | None = None
    supersede_active_task: bool = False

    def to_bridge_session_overrides(self) -> dict[str, Any]:
        return {
            "skip_design": self.skip_design,
            "design_later": self.design_later,
            "force_phase": self.force_phase,
            "human_approved_destructive_recovery": False,
        }


@dataclass(frozen=True)
class ExecutorContext:
    workspace_root: str
    correlation_id: str | None = None
    session: SessionOptions = field(default_factory=SessionOptions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutorContext:
        session_data = data.get("session") or data.get("session_options") or {}
        return cls(
            workspace_root=data["workspace_root"],
            correlation_id=data.get("correlation_id"),
            session=SessionOptions(
                skip_design=bool(session_data.get("skip_design", False)),
                design_later=bool(session_data.get("design_later", False)),
                force_phase=session_data.get("force_phase"),
                supersede_active_task=bool(session_data.get("supersede_active_task", False)),
            ),
        )


@dataclass
class StartupResult:
    ok: bool = False
    correlation_id: str = ""
    workspace_root: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    bootstrap_invoked: bool = False
    sync_invoked: bool = False
    project_state: str = ""
    doctor_summary: str = ""
    files_touched: list[str] = field(default_factory=list)
    bridge_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "correlation_id": self.correlation_id,
            "workspace_root": self.workspace_root,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "bootstrap_invoked": self.bootstrap_invoked,
            "sync_invoked": self.sync_invoked,
            "project_state": self.project_state,
            "doctor_summary": self.doctor_summary,
            "files_touched": list(self.files_touched),
            "bridge_codes": list(self.bridge_codes),
        }
