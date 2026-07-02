"""Bridge orchestration (Executor Spec §5.3, §5.4)."""

from vespawd_executor.orchestration.complete import orchestrate_phase_complete
from vespawd_executor.orchestration.documenter import orchestrate_pre_documenter
from vespawd_executor.orchestration.finalize import orchestrate_completion
from vespawd_executor.orchestration.gate import run_pre_implement_check
from vespawd_executor.orchestration.implement import orchestrate_post_implement
from vespawd_executor.orchestration.ingest import (
    orchestrate_master_prompt_from_text,
    orchestrate_master_prompt_ingest,
)
from vespawd_executor.orchestration.types import (
    CompleteOrchestrationResult,
    CompletionResult,
    DocumenterResult,
    GateResult,
    IngestOrchestrationResult,
    PostImplementResult,
    RecoveryAction,
)

__all__ = [
    "CompleteOrchestrationResult",
    "CompletionResult",
    "DocumenterResult",
    "GateResult",
    "IngestOrchestrationResult",
    "PostImplementResult",
    "RecoveryAction",
    "orchestrate_completion",
    "orchestrate_master_prompt_from_text",
    "orchestrate_master_prompt_ingest",
    "orchestrate_phase_complete",
    "orchestrate_post_implement",
    "orchestrate_pre_documenter",
    "run_pre_implement_check",
]
