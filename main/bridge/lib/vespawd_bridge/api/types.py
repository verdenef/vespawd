"""Public API types (§3.1, §3.4, §9.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SessionOverrides:
    skip_design: bool = False
    design_later: bool = False
    force_phase: str | None = None
    human_approved_destructive_recovery: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SessionOverrides:
        if not data:
            return cls()
        return cls(
            skip_design=bool(data.get("skip_design", False)),
            design_later=bool(data.get("design_later", False)),
            force_phase=data.get("force_phase"),
            human_approved_destructive_recovery=bool(
                data.get("human_approved_destructive_recovery", False)
            ),
        )


@dataclass(frozen=True)
class BridgeContext:
    workspace_root: str
    correlation_id: str | None = None
    session_overrides: SessionOverrides = field(default_factory=SessionOverrides)
    executor_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeContext:
        return cls(
            workspace_root=data["workspace_root"],
            correlation_id=data.get("correlation_id"),
            session_overrides=SessionOverrides.from_dict(data.get("session_overrides")),
            executor_metadata=dict(data.get("executor_metadata") or {}),
        )


@dataclass
class RecoveryHint:
    code: str
    action: str
    retry_operation: str | None = None
    destructive: bool = False

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "code": self.code,
            "action": self.action,
            "destructive": self.destructive,
        }
        if self.retry_operation:
            out["retry_operation"] = self.retry_operation
        return out


@dataclass
class BridgeResult:
    ok: bool = False
    operation: str = ""
    correlation_id: str = ""
    codes: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    vedaws_task_id: str = ""
    project_state: str = ""
    doctor_summary: str = ""
    files_touched: list[str] = field(default_factory=list)
    recovery: list[RecoveryHint] = field(default_factory=list)
    duration_ms: int = 0
    vedaws_commands_run: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "operation": self.operation,
            "correlation_id": self.correlation_id,
            "codes": list(self.codes),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "vedaws_task_id": self.vedaws_task_id,
            "project_state": self.project_state,
            "doctor_summary": self.doctor_summary,
            "files_touched": list(self.files_touched),
            "recovery": [hint.to_dict() for hint in self.recovery],
            "duration_ms": self.duration_ms,
            "vedaws_commands_run": list(self.vedaws_commands_run),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeResult:
        recovery = [
            RecoveryHint(
                code=item["code"],
                action=item["action"],
                retry_operation=item.get("retry_operation"),
                destructive=bool(item.get("destructive", False)),
            )
            for item in data.get("recovery", [])
        ]
        return cls(
            ok=bool(data.get("ok", False)),
            operation=str(data.get("operation", "")),
            correlation_id=str(data.get("correlation_id", "")),
            codes=list(data.get("codes", [])),
            blockers=list(data.get("blockers", [])),
            warnings=list(data.get("warnings", [])),
            vedaws_task_id=str(data.get("vedaws_task_id", "")),
            project_state=str(data.get("project_state", "")),
            doctor_summary=str(data.get("doctor_summary", "")),
            files_touched=list(data.get("files_touched", [])),
            recovery=recovery,
            duration_ms=int(data.get("duration_ms", 0)),
            vedaws_commands_run=list(data.get("vedaws_commands_run", [])),
        )


@dataclass(frozen=True)
class BootstrapInput:
    project_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BootstrapInput:
        if not data:
            return cls()
        return cls(project_name=data.get("project_name"))


@dataclass(frozen=True)
class MasterPromptIngest:
    current_task_goal: str
    current_task_acceptance_criteria: str
    current_task_constraints: str | None = None
    current_task_notes: str | None = None
    project_context_product_name: str | None = None
    phase_hint: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MasterPromptIngest:
        current_task = data.get("current_task", data)
        return cls(
            current_task_goal=current_task["goal"],
            current_task_acceptance_criteria=current_task.get("acceptance_criteria", ""),
            current_task_constraints=current_task.get("constraints"),
            current_task_notes=current_task.get("notes"),
            project_context_product_name=data.get("project_context", {}).get("product_name")
            if isinstance(data.get("project_context"), dict)
            else data.get("project_context_product_name"),
            phase_hint=data.get("phase_hint"),
        )


@dataclass(frozen=True)
class SyncInput:
    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SyncInput:
        return cls()


@dataclass(frozen=True)
class ImplementGateInput:
    current_task: str
    skip_design: bool = False
    design_later: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImplementGateInput:
        current_task = data.get("current_task", "")
        if isinstance(current_task, dict):
            current_task = current_task.get("text", str(current_task))
        return cls(
            current_task=str(current_task),
            skip_design=bool(data.get("skip_design", False)),
            design_later=bool(data.get("design_later", False)),
        )


@dataclass(frozen=True)
class PostImplementInput:
    vedaws_task_id: str
    changed_paths: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PostImplementInput:
        return cls(
            vedaws_task_id=data["vedaws_task_id"],
            changed_paths=list(data.get("changed_paths", [])),
        )


@dataclass(frozen=True)
class PhaseCompleteInput:
    vedaws_task_id: str
    outcome: str
    reason: str | None = None
    human_gate: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhaseCompleteInput:
        return cls(
            vedaws_task_id=data["vedaws_task_id"],
            outcome=data["outcome"],
            reason=data.get("reason"),
            human_gate=bool(data.get("human_gate", True)),
        )


@dataclass(frozen=True)
class DocumenterGateInput:
    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DocumenterGateInput:
        return cls()
