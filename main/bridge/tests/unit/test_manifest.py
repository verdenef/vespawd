"""Unit tests — manifest loader (§11.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.manifest.loader import load_manifest


def test_load_manifest_sidecar(workspace_root: Path) -> None:
    model, err = load_manifest(workspace_root)
    assert err is None
    assert model is not None
    assert model.workflow_id == "software"
    assert model.layout == "sidecar"
    assert len(model.phase_map) >= 7


def test_missing_manifest(tmp_path: Path) -> None:
    model, err = load_manifest(tmp_path)
    assert model is None
    assert err == "missing_manifest"
