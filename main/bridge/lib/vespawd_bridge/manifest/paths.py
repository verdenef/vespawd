"""Path resolver (§3.2, §5.2)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vespawd_bridge.manifest.model import ManifestModel


@dataclass(frozen=True)
class ResolvedPaths:
    pos_root: Path
    vedaws_project_root: Path
    userspace_root: Path
    manifest_path: Path
    current_task_path: Path
    status_path: Path
    handoff_path: Path
    design_gate_path: Path
    project_context_path: Path
    layout: str


def _resolve_relative(base: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def resolve_paths(workspace_root: Path, manifest: ManifestModel) -> ResolvedPaths:
    workspace_root = workspace_root.resolve()
    manifest_path = Path(manifest.manifest_path).resolve()

    if manifest.vedaws_project_root == ".":
        vedaws_project_root = manifest_path.parent.parent
    else:
        vedaws_project_root = _resolve_relative(workspace_root, manifest.vedaws_project_root)

    if manifest.layout == "integrated":
        pos_root = vedaws_project_root
    else:
        pos_root = _resolve_relative(vedaws_project_root, manifest.pos_root)

    userspace_root = vedaws_project_root / "src"
    if not userspace_root.is_dir():
        alt = workspace_root / "src"
        if alt.is_dir():
            userspace_root = alt.resolve()

    return ResolvedPaths(
        pos_root=pos_root,
        vedaws_project_root=vedaws_project_root,
        userspace_root=userspace_root.resolve(),
        manifest_path=manifest_path,
        current_task_path=_resolve_relative(pos_root, manifest.current_task),
        status_path=_resolve_relative(pos_root, manifest.status),
        handoff_path=_resolve_relative(pos_root, manifest.handoff),
        design_gate_path=_resolve_relative(pos_root, manifest.design_gate),
        project_context_path=pos_root / ".ai" / "project_context.md",
        layout=manifest.layout,
    )
