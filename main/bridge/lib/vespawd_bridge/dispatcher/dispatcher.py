"""Operation dispatcher (§1.4)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from vespawd_bridge import __version__, codes
from vespawd_bridge.api.types import (
    BootstrapInput,
    BridgeContext,
    BridgeResult,
    DocumenterGateInput,
    ImplementGateInput,
    MasterPromptIngest,
    PhaseCompleteInput,
    PostImplementInput,
    SyncInput,
)
from vespawd_bridge.cli.adapter import CliAdapter
from vespawd_bridge.logging.logger import BridgeLogger
from vespawd_bridge.manifest.loader import load_manifest
from vespawd_bridge.manifest.paths import resolve_paths
from vespawd_bridge.operations.context import HandlerContext
from vespawd_bridge.operations import (
    handle_bootstrap,
    handle_ingest_master_prompt,
    handle_post_implement,
    handle_post_phase_complete,
    handle_pre_documenter,
    handle_pre_implement_check,
    handle_sync_status,
)
from vespawd_bridge.recovery.engine import RecoveryTracker, hints_for_codes
from vespawd_bridge.validation.engine import validate_layout, validate_version, validate_compat_vedaws
from vespawd_bridge.cli.parse import parse_vedaws_version

OFFLINE_OPERATIONS = frozenset({"sync_status"})


def _read_impl_version() -> str:
    version_path = Path(__file__).resolve().parents[3] / "spec" / "VERSION"
    if version_path.is_file():
        return version_path.read_text(encoding="utf-8").strip()
    return __version__


class Dispatcher:
    _recovery_tracker = RecoveryTracker()

    def dispatch(self, operation: str, context: BridgeContext, payload) -> BridgeResult:
        start = time.perf_counter()
        correlation_id = context.correlation_id or str(uuid.uuid4())
        workspace_root = Path(context.workspace_root).resolve()
        log_dir = workspace_root / "main" / "bridge" / "logs"
        logger = BridgeLogger(correlation_id, log_dir if log_dir.parent.is_dir() else None)

        result = BridgeResult(operation=operation, correlation_id=correlation_id)
        commands_run: list[str] = []

        try:
            logger.operation_start(operation, str(workspace_root))

            manifest, manifest_code = load_manifest(workspace_root)
            if manifest is None:
                result.ok = False
                result.codes.append(manifest_code or codes.MISSING_MANIFEST)
                result.blockers.append("manifest.toml missing or invalid")
                result.recovery = hints_for_codes(result.codes)
                result.duration_ms = int((time.perf_counter() - start) * 1000)
                logger.operation_end(result.ok, result.codes, result.duration_ms)
                return result

            logger.manifest_loaded(manifest.vespawd_version, manifest.layout)
            paths = resolve_paths(workspace_root, manifest)
            logger.paths_resolved(str(paths.pos_root), str(paths.vedaws_project_root))

            layout_val = validate_layout(paths)
            version_val = validate_version(manifest, _read_impl_version())
            if not layout_val.passed:
                result.ok = False
                result.codes.extend(layout_val.codes)
                result.blockers.extend(layout_val.messages)
                result.recovery = hints_for_codes(result.codes)
                result.duration_ms = int((time.perf_counter() - start) * 1000)
                logger.validation_fail(result.codes)
                logger.operation_end(result.ok, result.codes, result.duration_ms)
                return result

            if not version_val.passed:
                result.ok = False
                result.codes.extend(version_val.codes)
                result.blockers.extend(version_val.messages)
                result.recovery = hints_for_codes(result.codes)
                result.duration_ms = int((time.perf_counter() - start) * 1000)
                logger.validation_fail(result.codes)
                logger.operation_end(result.ok, result.codes, result.duration_ms)
                return result
            if version_val.codes:
                result.warnings.extend(version_val.messages)

            cli = CliAdapter(manifest, paths.vedaws_project_root, logger, commands_run)
            ping = cli.ping()
            vedaws_available = ping.exit_code == 0 and not ping.timed_out
            if vedaws_available:
                compat_val = validate_compat_vedaws(manifest, parse_vedaws_version(ping.stdout))
                if compat_val.codes:
                    result.warnings.extend(compat_val.messages)
            if not vedaws_available and operation not in OFFLINE_OPERATIONS:
                result.ok = False
                code = codes.CLI_TIMEOUT if ping.timed_out else codes.VEDAWS_MISSING
                result.codes.append(code)
                result.blockers.append("Vedaws CLI unavailable")
                result.recovery = hints_for_codes(result.codes)
                result.vedaws_commands_run = commands_run
                result.duration_ms = int((time.perf_counter() - start) * 1000)
                logger.operation_end(result.ok, result.codes, result.duration_ms)
                return result

            handler_ctx = HandlerContext(
                manifest=manifest,
                paths=paths,
                cli=cli,
                logger=logger,
                implementation_version=_read_impl_version(),
                vedaws_available=vedaws_available,
                commands_run=commands_run,
                session_overrides=context.session_overrides,
                recovery_tracker=self._recovery_tracker,
            )

            handlers = {
                "bootstrap": lambda: handle_bootstrap(handler_ctx, payload, correlation_id),
                "ingest_master_prompt": lambda: handle_ingest_master_prompt(
                    handler_ctx, payload, correlation_id
                ),
                "sync_status": lambda: handle_sync_status(handler_ctx, correlation_id, payload),
                "pre_implement_check": lambda: handle_pre_implement_check(
                    handler_ctx, payload, correlation_id
                ),
                "post_implement": lambda: handle_post_implement(handler_ctx, payload, correlation_id),
                "post_phase_complete": lambda: handle_post_phase_complete(
                    handler_ctx, payload, correlation_id
                ),
                "pre_documenter": lambda: handle_pre_documenter(handler_ctx, payload, correlation_id),
            }

            result = handlers[operation]()
            result.correlation_id = correlation_id
            result.vedaws_commands_run = commands_run
            if not result.recovery and not result.ok:
                result.recovery = hints_for_codes(result.codes)

        except Exception as exc:  # noqa: BLE001
            result.ok = False
            result.codes.append(codes.INTERNAL_ERROR)
            result.blockers.append(str(exc))
            result.recovery = hints_for_codes(result.codes)
            logger.error("internal_error", error=str(exc))

        result.duration_ms = int((time.perf_counter() - start) * 1000)
        logger.operation_end(result.ok, result.codes, result.duration_ms)
        return result
