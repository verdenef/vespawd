"""Shared handler context."""

from __future__ import annotations

from dataclasses import dataclass, field

from vespawd_bridge.api.types import BridgeResult, SessionOverrides
from vespawd_bridge.cli.adapter import CliAdapter
from vespawd_bridge.logging.logger import BridgeLogger
from vespawd_bridge.recovery.engine import RecoveryTracker
from vespawd_bridge.manifest.model import ManifestModel
from vespawd_bridge.manifest.paths import ResolvedPaths


@dataclass
class HandlerContext:
    manifest: ManifestModel
    paths: ResolvedPaths
    cli: CliAdapter
    logger: BridgeLogger
    implementation_version: str
    vedaws_available: bool = True
    commands_run: list[str] = field(default_factory=list)
    session_overrides: SessionOverrides = field(default_factory=SessionOverrides)
    recovery_tracker: RecoveryTracker | None = None

    def base_result(self, operation: str, correlation_id: str) -> BridgeResult:
        return BridgeResult(operation=operation, correlation_id=correlation_id)


def apply_validation(result: BridgeResult, validation) -> None:
    result.codes.extend(validation.codes)
    for message in validation.messages:
        if validation.passed:
            result.warnings.append(message)
        else:
            result.blockers.append(message)


def truncate_doctor(summary: str, max_chars: int) -> str:
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 3] + "..."
