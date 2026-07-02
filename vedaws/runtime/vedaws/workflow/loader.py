"""Load workflow definitions from the project workflows directory."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.workflow.manifest import WORKFLOW_MANIFEST_SUFFIX, parse_workflow_manifest
from vedaws.workflow.models import WorkflowDefinition

logger = logging.getLogger("vedaws.workflow")


@dataclass
class WorkflowLoadResult:
    workflows: list[WorkflowDefinition] = field(default_factory=list)
    invalid: list[tuple[Path, str]] = field(default_factory=list)
    duplicates: list[tuple[str, Path, Path]] = field(default_factory=list)


def load_workflow_definitions(workflows_dir: Path) -> WorkflowLoadResult:
    result = WorkflowLoadResult()
    if not workflows_dir.is_dir():
        logger.debug("Workflows directory does not exist: %s", workflows_dir)
        return result

    seen: dict[str, Path] = {}
    for path in sorted(workflows_dir.rglob(f"*{WORKFLOW_MANIFEST_SUFFIX}")):
        definition, error = parse_workflow_manifest(path)
        if error or definition is None:
            result.invalid.append((path, error or "unknown error"))
            logger.warning("Invalid workflow manifest %s: %s", path, error)
            continue
        if definition.id in seen:
            result.duplicates.append((definition.id, seen[definition.id], path))
            logger.warning("Duplicate workflow id '%s' at %s", definition.id, path)
            continue
        seen[definition.id] = path
        result.workflows.append(definition)

    result.workflows.sort(key=lambda workflow: workflow.id)
    logger.info("Loaded %d workflow definition(s)", len(result.workflows))
    return result
