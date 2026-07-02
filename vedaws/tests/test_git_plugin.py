"""Git plugin tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from vedaws.cli.app import main
from vedaws.project.init import init_project
from vedaws.runtime.bootstrap import bootstrap

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@vedaws.local"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Vedaws Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_git_plugin_activates_and_registers_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _init_git_repo(tmp_path)
    init_project(tmp_path)
    context = bootstrap(tmp_path)
    git_record = context.registry.get("git")
    assert git_record is not None
    assert git_record.is_active
    assert context.worker_registry.get("git.status") is not None
    assert context.worker_registry.get("git.commit") is not None


def test_git_status_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _init_git_repo(tmp_path)
    init_project(tmp_path)
    assert main(["git", "status", "--path", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "branch" in output.lower() or "detached" in output.lower()


def test_git_branch_create_and_commit(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _init_git_repo(tmp_path)
    init_project(tmp_path)
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")

    assert main(["git", "branch", "--create", "feature/test", "--path", str(tmp_path)]) == 0
    assert (
        main(
            [
                "git",
                "commit",
                "-m",
                "Initial commit",
                "--stage-all",
                "--path",
                str(tmp_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert output


def test_git_status_fails_outside_repository(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["git", "status", "--path", str(tmp_path)]) == 1


def test_git_status_worker_executes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _init_git_repo(tmp_path)
    init_project(tmp_path)
    context = bootstrap(tmp_path)
    worker = context.worker_registry.get("git.status")
    assert worker is not None
    from vedaws.workflow.models import TaskDefinition
    from vedaws.workers.execution import TaskDispatch

    dispatch = TaskDispatch(
        workflow_id="test",
        task_id="status",
        task=TaskDefinition(id="status", name="Status", capability="git-status"),
        instructions=str(tmp_path),
    )
    outcome = worker.execute(dispatch)
    assert outcome.status.is_success


def test_git_plugin_info_lists_commands(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["plugins", "info", "git", "--path", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "git.status" in output
    assert "Commands:" in output
