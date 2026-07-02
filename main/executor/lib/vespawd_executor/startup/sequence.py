"""Startup orchestration (Executor Spec §3.6–3.7)."""

from __future__ import annotations

import uuid
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext, SessionOptions, StartupResult
from vespawd_executor.bridge.client import BridgeClient
from vespawd_executor.bridge.interpret import merge_bridge_into_startup, should_block_implement
from vespawd_executor.paths.resolver import WorkspacePaths, discover_workspace_root, resolve_workspace_paths
from vespawd_executor.startup.validate import validate_startup


def run_startup(
    workspace_root: Path | str | None = None,
    *,
    session: SessionOptions | None = None,
    correlation_id: str | None = None,
) -> StartupResult:
    """
    Complete Executor startup before userspace edits (§3).

    Resolves paths, validates layout, bootstraps Vedaws if needed, syncs status.
    """
    result = StartupResult()
    session = session or SessionOptions()
    result.correlation_id = correlation_id or str(uuid.uuid4())

    if workspace_root is None:
        discovered = discover_workspace_root()
        if discovered is None:
            result.blockers.append("Could not discover workspace root (main/bridge/manifest.toml)")
            return result
        workspace_root = discovered
    else:
        workspace_root = Path(workspace_root)

    result.workspace_root = str(workspace_root.resolve())

    try:
        paths = resolve_workspace_paths(workspace_root)
    except FileNotFoundError as exc:
        result.blockers.append(str(exc))
        return result

    validation = validate_startup(paths, session)
    result.warnings.extend(validation.warnings)
    if not validation.passed:
        result.blockers.extend(validation.blockers)
        return result

    ctx = ExecutorContext(
        workspace_root=result.workspace_root,
        correlation_id=result.correlation_id,
        session=session,
    )
    bridge = BridgeClient(paths.bridge_cli, paths.workspace_root)

    vedaws_marker = paths.vedaws_project_root / ".vedaws" / "project.toml"
    if not vedaws_marker.is_file():
        boot_payload: dict = {}
        if paths.project_context_path.is_file():
            from vespawd_executor.paths.resolver import parse_project_context

            info = parse_project_context(paths.project_context_path)
            if info.product_name:
                boot_payload["project_name"] = info.product_name

        boot = bridge.invoke("bootstrap", ctx, boot_payload or None)
        result.bootstrap_invoked = True
        result.bridge_codes.extend(boot.codes)
        result.files_touched.extend(boot.files_touched)
        result.project_state = boot.project_state or result.project_state
        result.doctor_summary = boot.doctor_summary or result.doctor_summary

        blockers, warnings, ok = merge_bridge_into_startup(
            result.blockers, result.warnings, boot
        )
        result.blockers = blockers
        result.warnings = warnings
        if not ok:
            result.ok = False
            return result

    sync = bridge.invoke("sync_status", ctx, {})
    result.sync_invoked = True
    result.bridge_codes.extend(sync.codes)
    result.files_touched.extend(sync.files_touched)
    result.project_state = sync.project_state or result.project_state
    result.doctor_summary = sync.doctor_summary or result.doctor_summary

    blockers, warnings, ok = merge_bridge_into_startup(result.blockers, result.warnings, sync)
    result.blockers = blockers
    result.warnings = warnings

    if should_block_implement(sync) and "doctor_blocked" in sync.codes:
        result.blockers.append("vedaws doctor reports blocking issues; resolve before implement")

    result.ok = ok and not result.blockers
    return result
