"""Workspace and path discovery (Executor Spec §3.5)."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestPointers:
    layout: str
    pos_root: str
    vedaws_project_root: str
    manifest_path: Path


@dataclass(frozen=True)
class ProjectContextInfo:
    mode: str | None
    application_code: str | None
    product_name: str | None
    raw_path: Path


@dataclass(frozen=True)
class WorkspacePaths:
    workspace_root: Path
    manifest: ManifestPointers
    pos_root: Path
    vedaws_project_root: Path
    userspace_root: Path
    bridge_root: Path
    bridge_cli: Path
    project_context_path: Path
    current_task_path: Path
    status_path: Path
    layout_from_manifest: str
    layout_from_context: str | None


def _resolve_relative(base: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def discover_workspace_root(start: Path | None = None) -> Path | None:
    """Walk upward from start (or cwd) to find main/bridge/manifest.toml."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        manifest = candidate / "main" / "bridge" / "manifest.toml"
        if manifest.is_file():
            return candidate
    return None


def load_manifest(manifest_path: Path) -> ManifestPointers:
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    vespawd = data.get("vespawd", {})
    pos = data.get("pos", {})
    vedaws = data.get("vedaws", {})
    return ManifestPointers(
        layout=str(vespawd.get("layout", "sidecar")),
        pos_root=str(pos.get("root", "../paws022")),
        vedaws_project_root=str(vedaws.get("project_root", ".")),
        manifest_path=manifest_path.resolve(),
    )


_MODE_RE = re.compile(r"^\s*\|\s*Mode\s*\|\s*([^|]+)\|", re.MULTILINE | re.IGNORECASE)
_APP_CODE_RE = re.compile(
    r"^\s*\|\s*Application code\s*\|\s*`?([^`|]+)`?\s*\|",
    re.MULTILINE | re.IGNORECASE,
)
_NAME_RE = re.compile(r"\*\*Name:\*\*\s*(\S+)")


def parse_project_context(path: Path) -> ProjectContextInfo:
    if not path.is_file():
        return ProjectContextInfo(mode=None, application_code=None, product_name=None, raw_path=path)
    text = path.read_text(encoding="utf-8", errors="replace")
    mode_match = _MODE_RE.search(text)
    app_match = _APP_CODE_RE.search(text)
    name_match = _NAME_RE.search(text)
    mode = mode_match.group(1).strip().lower() if mode_match else None
    app_code = app_match.group(1).strip() if app_match else None
    name = name_match.group(1).strip() if name_match else None
    return ProjectContextInfo(
        mode=mode,
        application_code=app_code,
        product_name=name,
        raw_path=path,
    )


def resolve_workspace_paths(workspace_root: Path) -> WorkspacePaths:
    workspace_root = workspace_root.resolve()
    manifest_path = workspace_root / "main" / "bridge" / "manifest.toml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Bridge manifest not found: {manifest_path}")

    manifest = load_manifest(manifest_path)
    bridge_root = manifest_path.parent

    if manifest.vedaws_project_root == ".":
        vedaws_project_root = bridge_root.parent
    else:
        vedaws_project_root = _resolve_relative(workspace_root, manifest.vedaws_project_root)

    if manifest.layout == "integrated":
        pos_root = vedaws_project_root
    else:
        pos_root = _resolve_relative(vedaws_project_root, manifest.pos_root)

    project_context_path = pos_root / ".ai" / "project_context.md"
    context = parse_project_context(project_context_path)

    userspace_root = _resolve_userspace(
        workspace_root, vedaws_project_root, pos_root, manifest.layout, context
    )

    return WorkspacePaths(
        workspace_root=workspace_root,
        manifest=manifest,
        pos_root=pos_root,
        vedaws_project_root=vedaws_project_root,
        userspace_root=userspace_root,
        bridge_root=bridge_root,
        bridge_cli=bridge_root / "bin" / "bridge",
        project_context_path=project_context_path,
        current_task_path=pos_root / "tasks" / "current_task.md",
        status_path=pos_root / "tasks" / "status.md",
        layout_from_manifest=manifest.layout,
        layout_from_context=context.mode,
    )


def _resolve_userspace(
    workspace_root: Path,
    vedaws_root: Path,
    pos_root: Path,
    manifest_layout: str,
    context: ProjectContextInfo,
) -> Path:
    if context.application_code:
        raw = context.application_code.strip().strip("`")
        if raw:
            if Path(raw).is_absolute():
                return Path(raw).resolve()
            return _resolve_relative(pos_root, raw)

    if manifest_layout == "sidecar":
        return (vedaws_root / "src").resolve()

    return (pos_root / "src").resolve()
