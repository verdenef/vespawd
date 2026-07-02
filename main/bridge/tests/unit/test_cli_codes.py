"""Unit tests — CLI error mapping (§11.1)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.cli.adapter import CliAdapter, CliResult
from vespawd_bridge.logging.logger import BridgeLogger
from vespawd_bridge.manifest.loader import load_manifest
from vespawd_bridge.manifest.paths import resolve_paths


def test_cli_timeout_code(workspace_root) -> None:
    manifest, _ = load_manifest(workspace_root)
    paths = resolve_paths(workspace_root, manifest)
    logger = BridgeLogger("test")
    adapter = CliAdapter(manifest, paths.vedaws_project_root, logger, [])
    result = CliResult(exit_code=-1, stdout="", stderr="", timed_out=True)
    assert adapter.cli_result_code(result) == codes.CLI_TIMEOUT
