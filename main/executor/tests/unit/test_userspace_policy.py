"""Userspace path policy unit tests (§7.1, §7.2)."""

from __future__ import annotations

from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.policy.userspace import PathClass, check_changed_paths, classify_path


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


def test_userspace_allowed(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "main/src/app.py").verdict is PathClass.ALLOWED


def test_main_docs_allowed(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "main/docs/architecture/API.md").verdict is PathClass.ALLOWED


def test_paws_docs_design_tasks_allowed(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "paws022/docs/architecture.md").verdict is PathClass.ALLOWED
    assert classify_path(paths, "paws022/design/DESIGN.md").verdict is PathClass.ALLOWED
    assert classify_path(paths, "paws022/tasks/current_task.md").verdict is PathClass.ALLOWED


def test_project_context_allowed_but_kernel_forbidden(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "paws022/.ai/project_context.md").verdict is PathClass.ALLOWED
    assert classify_path(paths, "paws022/.ai/executor_rules.md").verdict is PathClass.FORBIDDEN


def test_wrong_userspace_forbidden_in_sidecar(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "paws022/src/foo.py").verdict is PathClass.FORBIDDEN


def test_runtime_and_frozen_forbidden(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "main/.vedaws/state.json").verdict is PathClass.FORBIDDEN
    assert classify_path(paths, "vedaws/runtime/x.py").verdict is PathClass.FORBIDDEN


def test_outside_roots_unknown(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    assert classify_path(paths, "README.md").verdict is PathClass.UNKNOWN


def test_check_changed_paths_aggregates(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    report = check_changed_paths(
        paths,
        [
            "main/src/service.py",
            "paws022/.ai/coding_rules.md",
            "README.md",
            "  ",
        ],
    )
    assert len(report.allowed) == 1
    assert len(report.forbidden) == 1
    assert len(report.unknown) == 1
    assert report.has_violations
    assert report.blockers()
    assert report.warnings()


def test_check_changed_paths_idempotent(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    changed = ["main/src/a.py", "main/src/b.py"]
    first = check_changed_paths(paths, changed)
    second = check_changed_paths(paths, changed)
    assert [v.verdict for v in first.verdicts] == [v.verdict for v in second.verdicts]
