"""Allowed / forbidden directory policy for userspace edits (Executor Spec §7.1, §7.2).

The Executor is IDE-neutral: it does not itself write application code. This module
classifies proposed changed paths so the Executor can guard §7 before invoking Bridge
post-implementation hooks. Classification is read-only and layout-aware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from vespawd_executor.paths.resolver import WorkspacePaths


class PathClass(str, Enum):
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PathVerdict:
    path: str
    resolved: str
    verdict: PathClass
    reason: str


@dataclass
class PolicyReport:
    allowed: list[PathVerdict] = field(default_factory=list)
    forbidden: list[PathVerdict] = field(default_factory=list)
    unknown: list[PathVerdict] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.forbidden)

    @property
    def verdicts(self) -> list[PathVerdict]:
        return [*self.allowed, *self.forbidden, *self.unknown]

    def blockers(self) -> list[str]:
        return [f"forbidden edit: {v.path} ({v.reason})" for v in self.forbidden]

    def warnings(self) -> list[str]:
        return [f"unclassified edit: {v.path} ({v.reason})" for v in self.unknown]


def _resolve(workspace_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    return (workspace_root / candidate).resolve()


def _within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def classify_path(paths: WorkspacePaths, raw_path: str) -> PathVerdict:
    """Classify a single changed path against §7.1 (allowed) and §7.2 (forbidden)."""
    resolved = _resolve(paths.workspace_root, raw_path)
    resolved_str = str(resolved).replace("\\", "/")

    pos_root = paths.pos_root
    main_root = paths.vedaws_project_root
    ai_dir = pos_root / ".ai"

    # §7.1: project_context.md is the single writable file under the kernel .ai dir.
    if resolved == (ai_dir / "project_context.md").resolve():
        return PathVerdict(raw_path, resolved_str, PathClass.ALLOWED, "project_context.md")

    # §7.2 forbidden checks first (more specific than allowed roots).
    if _within(resolved, ai_dir):
        return PathVerdict(raw_path, resolved_str, PathClass.FORBIDDEN, "kernel .ai (not project_context.md)")

    if _within(resolved, (main_root / ".vedaws")):
        return PathVerdict(raw_path, resolved_str, PathClass.FORBIDDEN, "runtime-managed main/.vedaws")

    if _within(resolved, (paths.workspace_root / "vedaws")):
        return PathVerdict(raw_path, resolved_str, PathClass.FORBIDDEN, "frozen vedaws reference")

    if paths.layout_from_manifest == "sidecar" and _within(resolved, (pos_root / "src")):
        return PathVerdict(raw_path, resolved_str, PathClass.FORBIDDEN, "wrong userspace (paws022/src in sidecar)")

    # §7.1 allowed roots.
    allowed_roots = [
        (paths.userspace_root, "userspace"),
        (main_root / "docs", "main/docs"),
        (pos_root / "docs", "paws022/docs"),
        (pos_root / "design", "paws022/design"),
        (pos_root / "tasks", "paws022/tasks"),
    ]
    for root, label in allowed_roots:
        if _within(resolved, root.resolve()):
            return PathVerdict(raw_path, resolved_str, PathClass.ALLOWED, label)

    return PathVerdict(raw_path, resolved_str, PathClass.UNKNOWN, "outside allowed and forbidden roots")


def check_changed_paths(paths: WorkspacePaths, changed_paths: list[str]) -> PolicyReport:
    """Classify a set of changed paths into a §7 policy report (idempotent, read-only)."""
    report = PolicyReport()
    for raw in changed_paths:
        if not raw or not str(raw).strip():
            continue
        verdict = classify_path(paths, str(raw).strip())
        if verdict.verdict is PathClass.ALLOWED:
            report.allowed.append(verdict)
        elif verdict.verdict is PathClass.FORBIDDEN:
            report.forbidden.append(verdict)
        else:
            report.unknown.append(verdict)
    return report
