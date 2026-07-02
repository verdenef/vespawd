"""Unit tests — path resolver (§11.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.manifest.loader import load_manifest
from vespawd_bridge.manifest.paths import resolve_paths


def test_resolve_paths_sidecar(workspace_root: Path) -> None:
    manifest, _ = load_manifest(workspace_root)
    assert manifest is not None
    paths = resolve_paths(workspace_root, manifest)
    assert paths.pos_root.name == "paws022"
    assert paths.vedaws_project_root.name == "main"
    assert paths.layout == "sidecar"
