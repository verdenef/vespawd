"""Master Prompt ingest orchestration (Executor Spec §5.3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient
from vespawd_executor.bridge.interpret import apply_bridge_result, should_block_implement
from vespawd_executor.orchestration.types import IngestOrchestrationResult
from vespawd_executor.parse import parse_master_prompt
from vespawd_executor.parse.engine import to_ingest_payload
from vespawd_executor.parse.types import ParsedMasterPrompt
from vespawd_executor.paths.resolver import WorkspacePaths, resolve_workspace_paths
from vespawd_executor.sync.engine import seed_handoff_from_parse, sync_paws_scheduler


def _bridge_client(paths: WorkspacePaths) -> BridgeClient:
    return BridgeClient(paths.bridge_cli, paths.workspace_root)


def orchestrate_master_prompt_ingest(
    parsed: ParsedMasterPrompt,
    paths: WorkspacePaths,
    ctx: ExecutorContext,
    *,
    repo_path: str | None = None,
    started_at: date | None = None,
    synced_at: datetime | None = None,
) -> IngestOrchestrationResult:
    """
    Full §5.3 sequence:
    1. PAWS scheduler writes
    2. bridge.ingest_master_prompt
    3. bridge.sync_status
    4. HANDOFF seed
    """
    result = IngestOrchestrationResult(
        correlation_id=ctx.correlation_id or str(uuid.uuid4()),
    )
    blockers: list[str] = []
    warnings: list[str] = []
    recovery = []
    block_implement = False
    ts = synced_at or datetime.now(timezone.utc)

    paws = sync_paws_scheduler(parsed, paths, started_at=started_at)
    result.paws_sync = paws
    result.steps_completed.append("paws_scheduler")
    warnings.extend(paws.warnings)

    bridge = _bridge_client(paths)
    ingest_payload = to_ingest_payload(parsed)
    ingest = bridge.invoke("ingest_master_prompt", ctx, ingest_payload)
    result.ingest = ingest
    result.steps_completed.append("bridge.ingest_master_prompt")
    blockers, warnings, recovery, block_implement = apply_bridge_result(
        blockers=blockers,
        warnings=warnings,
        recovery=recovery,
        bridge=ingest,
        block_implement=block_implement,
    )
    if ingest.vedaws_task_id:
        result.vedaws_task_id = ingest.vedaws_task_id
    if ingest.project_state:
        result.project_state = ingest.project_state
    if ingest.doctor_summary:
        result.doctor_summary = ingest.doctor_summary

    sync = bridge.invoke("sync_status", ctx, {})
    result.sync_status = sync
    result.steps_completed.append("bridge.sync_status")
    blockers, warnings, recovery, block_implement = apply_bridge_result(
        blockers=blockers,
        warnings=warnings,
        recovery=recovery,
        bridge=sync,
        block_implement=block_implement,
    )
    if sync.project_state:
        result.project_state = sync.project_state
    if sync.vedaws_task_id and not result.vedaws_task_id:
        result.vedaws_task_id = sync.vedaws_task_id

    _, handoff_warnings = seed_handoff_from_parse(
        parsed, paths, repo_path=repo_path, synced_at=ts
    )
    result.steps_completed.append("handoff_seed")
    warnings.extend(handoff_warnings)

    result.blockers = list(dict.fromkeys(blockers))
    result.warnings = list(dict.fromkeys(warnings))
    result.recovery = recovery
    result.block_implement = block_implement
    result.ok = paws.ok and not result.blockers
    return result


def orchestrate_master_prompt_from_text(
    text: str,
    workspace_root: Path | str,
    ctx: ExecutorContext | None = None,
    *,
    started_at: date | None = None,
    synced_at: datetime | None = None,
) -> IngestOrchestrationResult:
    """Parse + orchestrate; returns failed result when parse fails (§4.7)."""
    workspace_root = Path(workspace_root)
    parse_result = parse_master_prompt(text)
    correlation_id = (ctx.correlation_id if ctx else None) or str(uuid.uuid4())
    if not parse_result.ok or parse_result.parsed is None:
        return IngestOrchestrationResult(
            ok=False,
            block_implement=True,
            correlation_id=correlation_id,
            blockers=list(parse_result.errors),
            warnings=[],
        )

    paths = resolve_workspace_paths(workspace_root)
    exec_ctx = ctx or ExecutorContext(
        workspace_root=str(workspace_root.resolve()),
        correlation_id=correlation_id,
    )
    return orchestrate_master_prompt_ingest(
        parse_result.parsed,
        paths,
        exec_ctx,
        repo_path=str(workspace_root.resolve()),
        started_at=started_at,
        synced_at=synced_at,
    )
