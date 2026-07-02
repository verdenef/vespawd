"""Project detection within a workspace."""

from __future__ import annotations

from pathlib import Path

from vedaws.config.loader import load_project_section
from vedaws.config.paths import find_project_root, project_config_dir
from vedaws.project.model import ProjectContext
from vedaws.project.state.engine import StateEngine


def detect_project(
    workspace: Path | None = None, *, read_only: bool = False
) -> ProjectContext | None:
    workspace = workspace or Path.cwd()
    root = find_project_root(workspace)
    if root is None:
        return None

    section = load_project_section(root)
    if section is None:
        return None

    config_dir = project_config_dir(root)
    if config_dir is None:
        return None

    engine = StateEngine.load(config_dir, legacy_state=section.state)
    engine.validate()
    # Lazy import avoids workflow<->project package import cycles during module import.
    from vedaws.workflow.engine import WorkflowEngine

    workflow_engine = WorkflowEngine.load(config_dir, state_engine=engine)
    if not read_only:
        sync_manifest_state(root, engine)
    return ProjectContext(
        root=root,
        name=section.name,
        state_engine=engine,
        workflow_engine=workflow_engine,
    )


def sync_manifest_state(root: Path, engine: StateEngine) -> None:
    """Keep `project.toml` state aligned with authoritative `state.toml`.

    This is a best-effort compatibility sync for tools that still read state from
    the project manifest. The state machine remains authoritative.
    """
    from vedaws.config.paths import PROJECT_MANIFEST_FILE

    manifest_path = root / ".vedaws" / PROJECT_MANIFEST_FILE
    if not manifest_path.is_file():
        return

    text = manifest_path.read_text(encoding="utf-8")
    current_line = f'state = "{engine.current.value}"'
    if current_line in text:
        return

    lines = text.splitlines()
    updated: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("state ") or stripped.startswith("state="):
            updated.append(current_line)
            replaced = True
        else:
            updated.append(line)
    if not replaced and "[project]" in text:
        for index, line in enumerate(updated):
            if line.strip() == "[project]":
                updated.insert(index + 1, current_line)
                replaced = True
                break
    if replaced:
        manifest_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
