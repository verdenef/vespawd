"""Path discovery tests (§3.5)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.paths.resolver import (
    discover_workspace_root,
    parse_project_context,
    resolve_workspace_paths,
)


def test_discover_workspace_root(workspace_root: Path) -> None:
    found = discover_workspace_root(workspace_root / "main")
    assert found == workspace_root.resolve()


def test_resolve_sidecar_paths(fixture_workspace: Path) -> None:
    paths = resolve_workspace_paths(fixture_workspace)
    assert paths.pos_root.name == "paws022"
    assert paths.vedaws_project_root.name == "main"
    assert paths.userspace_root == (fixture_workspace / "main" / "src").resolve()
    assert paths.bridge_cli.is_file()


def test_parse_project_context_mode(fixture_workspace: Path) -> None:
    info = parse_project_context(fixture_workspace / "paws022" / ".ai" / "project_context.md")
    assert info.mode == "sidecar"
    assert info.product_name == "testapp"
    assert "main/src" in (info.application_code or "")
