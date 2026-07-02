"""Orchestration result types (Executor Spec §5.3, §5.4, §8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.policy.userspace import PolicyReport
from vespawd_executor.sync.types import PawsSyncResult


@dataclass
class RecoveryAction:
    code: str
    action: str
    retry_operation: str | None = None
    destructive: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecoveryAction:
        return cls(
            code=str(data.get("code", "")),
            action=str(data.get("action", "")),
            retry_operation=data.get("retry_operation"),
            destructive=bool(data.get("destructive", False)),
        )


@dataclass
class IngestOrchestrationResult:
    ok: bool = False
    block_implement: bool = False
    correlation_id: str = ""
    steps_completed: list[str] = field(default_factory=list)
    paws_sync: PawsSyncResult | None = None
    ingest: BridgeResultView | None = None
    sync_status: BridgeResultView | None = None
    vedaws_task_id: str = ""
    project_state: str = ""
    doctor_summary: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "block_implement": self.block_implement,
            "correlation_id": self.correlation_id,
            "steps_completed": list(self.steps_completed),
            "vedaws_task_id": self.vedaws_task_id,
            "project_state": self.project_state,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recovery": [
                {
                    "code": item.code,
                    "action": item.action,
                    "retry_operation": item.retry_operation,
                    "destructive": item.destructive,
                }
                for item in self.recovery
            ],
        }


@dataclass
class CompleteOrchestrationResult:
    ok: bool = False
    correlation_id: str = ""
    steps_completed: list[str] = field(default_factory=list)
    post_phase_complete: BridgeResultView | None = None
    sync_status: BridgeResultView | None = None
    project_state: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)


@dataclass
class PostImplementResult:
    """Post-implementation result (Executor Spec §7 guard + §8.3 hooks)."""

    ok: bool = False
    correlation_id: str = ""
    steps_completed: list[str] = field(default_factory=list)
    policy: PolicyReport | None = None
    progress_logged: bool = False
    progress_path: str = ""
    post_implement: BridgeResultView | None = None
    sync_status: BridgeResultView | None = None
    vedaws_task_id: str = ""
    project_state: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "correlation_id": self.correlation_id,
            "steps_completed": list(self.steps_completed),
            "progress_logged": self.progress_logged,
            "progress_path": self.progress_path,
            "vedaws_task_id": self.vedaws_task_id,
            "project_state": self.project_state,
            "policy": {
                "allowed": [v.path for v in self.policy.allowed],
                "forbidden": [v.path for v in self.policy.forbidden],
                "unknown": [v.path for v in self.policy.unknown],
            }
            if self.policy is not None
            else None,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recovery": [
                {
                    "code": item.code,
                    "action": item.action,
                    "retry_operation": item.retry_operation,
                    "destructive": item.destructive,
                }
                for item in self.recovery
            ],
        }


@dataclass
class CompletionResult:
    """Full completion sequence result (Executor Spec §5.4, §10.6)."""

    ok: bool = False
    correlation_id: str = ""
    steps_completed: list[str] = field(default_factory=list)
    phase_complete: CompleteOrchestrationResult | None = None
    handoff_path: str = ""
    handoff_refreshed: bool = False
    completed_log_path: str = ""
    completed_log_created: bool = False
    current_task_closed: bool = False
    project_state: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "correlation_id": self.correlation_id,
            "steps_completed": list(self.steps_completed),
            "handoff_path": self.handoff_path,
            "handoff_refreshed": self.handoff_refreshed,
            "completed_log_path": self.completed_log_path,
            "completed_log_created": self.completed_log_created,
            "current_task_closed": self.current_task_closed,
            "project_state": self.project_state,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass
class DocumenterResult:
    """pre_documenter gate result (Executor Spec §8.5)."""

    ok: bool = False
    correlation_id: str = ""
    check: BridgeResultView | None = None
    handoff_ready: bool = False
    artifacts_missing: bool = False
    handoff_stale: bool = False
    doctor_blocked: bool = False
    project_state: str = ""
    doctor_summary: str = ""
    files_touched: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "correlation_id": self.correlation_id,
            "handoff_ready": self.handoff_ready,
            "artifacts_missing": self.artifacts_missing,
            "handoff_stale": self.handoff_stale,
            "doctor_blocked": self.doctor_blocked,
            "project_state": self.project_state,
            "doctor_summary": self.doctor_summary,
            "files_touched": list(self.files_touched),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass
class GateResult:
    """pre_implement_check decision (Executor Spec §8.2)."""

    allow_implement: bool = False
    correlation_id: str = ""
    check: BridgeResultView | None = None
    vedaws_task_id: str = ""
    project_state: str = ""
    doctor_summary: str = ""
    design_gate_blocked: bool = False
    design_gate_overridden: bool = False
    workflow_ineligible: bool = False
    task_mismatch: bool = False
    doctor_blocked: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovery: list[RecoveryAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_implement": self.allow_implement,
            "correlation_id": self.correlation_id,
            "vedaws_task_id": self.vedaws_task_id,
            "project_state": self.project_state,
            "doctor_summary": self.doctor_summary,
            "design_gate_blocked": self.design_gate_blocked,
            "design_gate_overridden": self.design_gate_overridden,
            "workflow_ineligible": self.workflow_ineligible,
            "task_mismatch": self.task_mismatch,
            "doctor_blocked": self.doctor_blocked,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recovery": [
                {
                    "code": item.code,
                    "action": item.action,
                    "retry_operation": item.retry_operation,
                    "destructive": item.destructive,
                }
                for item in self.recovery
            ],
        }
