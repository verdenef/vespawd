"""Structured logging (§10)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BridgeLogger:
    def __init__(self, correlation_id: str, log_dir: Path | None = None) -> None:
        self.correlation_id = correlation_id
        self._logger = logging.getLogger(f"vespawd.bridge.{correlation_id}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()
        self._logger.propagate = False

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

        if log_dir is not None:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_dir / f"bridge-{correlation_id}.log", encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(file_handler)

    def _emit(self, level: str, event: str, fields: dict[str, Any]) -> None:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "correlation_id": self.correlation_id,
            "event": event,
            **fields,
        }
        line = json.dumps(payload, default=str)
        if level == "ERROR":
            self._logger.error(line)
        elif level == "WARN":
            self._logger.warning(line)
        elif level == "DEBUG":
            self._logger.debug(line)
        else:
            self._logger.info(line)

    def operation_start(self, operation: str, workspace_root: str) -> None:
        self._emit("INFO", "operation_start", {"operation": operation, "workspace_root": workspace_root})

    def manifest_loaded(self, version: str, layout: str) -> None:
        self._emit("INFO", "manifest_loaded", {"version": version, "layout": layout})

    def paths_resolved(self, pos_root: str, vedaws_project_root: str) -> None:
        self._emit(
            "INFO",
            "paths_resolved",
            {"pos_root": pos_root, "vedaws_project_root": vedaws_project_root},
        )

    def cli_invoke(self, argv: list[str]) -> None:
        self._emit("INFO", "cli_invoke", {"argv": argv})

    def cli_complete(self, exit_code: int, duration_ms: int) -> None:
        self._emit("INFO", "cli_complete", {"exit_code": exit_code, "duration_ms": duration_ms})

    def validation_fail(self, codes: list[str]) -> None:
        self._emit("WARN", "validation_fail", {"codes": codes})

    def projection_write(self, files_touched: list[str]) -> None:
        self._emit("INFO", "projection_write", {"files_touched": files_touched})

    def operation_end(self, ok: bool, codes: list[str], duration_ms: int) -> None:
        self._emit("INFO", "operation_end", {"ok": ok, "codes": codes, "duration_ms": duration_ms})

    def debug(self, message: str, **fields: Any) -> None:
        self._emit("DEBUG", "debug", {"message": message, **fields})

    def warn(self, message: str, **fields: Any) -> None:
        self._emit("WARN", "warn", {"message": message, **fields})

    def error(self, message: str, **fields: Any) -> None:
        self._emit("ERROR", "error", {"message": message, **fields})
