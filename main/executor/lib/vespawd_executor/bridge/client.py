"""Bridge subprocess client (Executor Spec §8, §14)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vespawd_executor.api.types import ExecutorContext, SessionOptions


@dataclass
class BridgeResultView:
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
    duration_ms: int = 0
    vedaws_commands_run: list[str] = field(default_factory=list)
    recovery: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeResultView:
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
            duration_ms=int(data.get("duration_ms", 0)),
            vedaws_commands_run=list(data.get("vedaws_commands_run", [])),
            recovery=list(data.get("recovery", [])),
            raw=data,
        )


class BridgeClient:
    """Invoke Bridge operations via the public CLI (no internal bridge imports)."""

    def __init__(self, bridge_cli: Path, workspace_root: Path) -> None:
        self.bridge_cli = bridge_cli
        self.workspace_root = workspace_root.resolve()

    def invoke(
        self,
        operation: str,
        ctx: ExecutorContext,
        payload: dict[str, Any] | None = None,
    ) -> BridgeResultView:
        if not self.bridge_cli.is_file():
            return BridgeResultView(
                ok=False,
                operation=operation,
                correlation_id=ctx.correlation_id or "",
                blockers=[f"Bridge CLI not found: {self.bridge_cli}"],
                codes=["bridge_missing"],
            )

        correlation_id = ctx.correlation_id or str(uuid.uuid4())
        context_data = {
            "workspace_root": str(self.workspace_root),
            "correlation_id": correlation_id,
            "session_overrides": ctx.session.to_bridge_session_overrides(),
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            context_file = tmp_path / "context.json"
            context_file.write_text(json.dumps(context_data), encoding="utf-8")

            argv = [
                sys.executable,
                str(self.bridge_cli),
                "invoke",
                operation,
                "--context",
                str(context_file),
            ]
            if payload:
                input_file = tmp_path / "input.json"
                input_file.write_text(json.dumps(payload), encoding="utf-8")
                argv.extend(["--input", str(input_file)])

            output_file = tmp_path / "result.json"
            argv.extend(["--output", str(output_file)])

            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if not output_file.is_file():
                return BridgeResultView(
                    ok=False,
                    operation=operation,
                    correlation_id=correlation_id,
                    blockers=[
                        completed.stderr.strip()
                        or completed.stdout.strip()
                        or "Bridge invoke produced no result"
                    ],
                    codes=["bridge_invoke_failed"],
                )

            data = json.loads(output_file.read_text(encoding="utf-8"))
            result = BridgeResultView.from_dict(data)
            result.correlation_id = correlation_id
            return result
