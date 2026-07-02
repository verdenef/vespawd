"""Git workers for workflow dispatch."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from git_plugin.errors import GitAuthError, GitError
from git_plugin.repository import GitRepository, find_git_executable
from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerCapability, WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType


def _git_metadata(
    *,
    worker_id: str,
    name: str,
    description: str,
    capability: str,
) -> WorkerMetadata:
    return WorkerMetadata(
        id=worker_id,
        name=name,
        description=description,
        version="0.1.0",
        worker_type=WorkerType.TOOL,
        capabilities=(WorkerCapability(work_type=capability, scope="repository"),),
        status=WorkerStatus.AVAILABLE,
        provider="git-plugin",
        source_path=Path("git_plugin"),
    )


class _GitWorkerBase(ExecutableWorker):
    capability: str = ""

    def __init__(self, *, worker_id: str, name: str, description: str, capability: str) -> None:
        self._metadata = _git_metadata(
            worker_id=worker_id,
            name=name,
            description=description,
            capability=capability,
        )

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        try:
            find_git_executable()
            return WorkerHealthReport(
                worker_id=self.id,
                health=WorkerHealth.HEALTHY,
                message="Git worker ready",
            )
        except GitError as exc:
            return WorkerHealthReport(
                worker_id=self.id,
                health=WorkerHealth.UNHEALTHY,
                message=str(exc),
            )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)

    def _open_repo(self, dispatch: TaskDispatch) -> GitRepository:
        root = Path(dispatch.instructions).resolve() if dispatch.instructions else Path.cwd()
        return GitRepository.open(root)


class GitStatusWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.status",
            name="Git Status Worker",
            description="Report repository status",
            capability="git-status",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            status = repo.status()
            return TaskOutcome.success(
                message=status.summary,
                branch=status.branch,
                detached=status.detached,
                clean=status.clean,
            )
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


class GitBranchWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.branch",
            name="Git Branch Worker",
            description="Inspect or create branches",
            capability="git-branch",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            branch_name = dispatch.instructions.strip()
            if branch_name:
                created = repo.create_branch(branch_name)
                return TaskOutcome.success(message=f"created branch {created}")
            branch = repo.current_branch()
            return TaskOutcome.success(message=branch or "detached HEAD", branch=branch)
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


class GitCommitWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.commit",
            name="Git Commit Worker",
            description="Stage and commit repository changes",
            capability="git-commit",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            message = dispatch.instructions.strip() or dispatch.task.description.strip()
            if not message:
                return TaskOutcome.failure(message="commit message is required in task instructions")
            repo.stage()
            result = repo.commit(message)
            return TaskOutcome.success(message=result)
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


class GitFetchWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.fetch",
            name="Git Fetch Worker",
            description="Fetch updates from a remote",
            capability="git-fetch",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            remote = dispatch.instructions.strip() or "origin"
            message = repo.fetch(remote=remote)
            return TaskOutcome.success(message=message)
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


class GitPullWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.pull",
            name="Git Pull Worker",
            description="Pull updates from a remote",
            capability="git-pull",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            remote = dispatch.instructions.strip() or "origin"
            message = repo.pull(remote=remote)
            return TaskOutcome.success(message=message)
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


class GitPushWorker(_GitWorkerBase):
    def __init__(self) -> None:
        super().__init__(
            worker_id="git.push",
            name="Git Push Worker",
            description="Push commits to a remote",
            capability="git-push",
        )

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        try:
            repo = self._open_repo(dispatch)
            remote = dispatch.instructions.strip() or "origin"
            message = repo.push(remote=remote)
            return TaskOutcome.success(message=message)
        except GitAuthError as exc:
            return TaskOutcome.failure(
                message=f"Push skipped — authentication not available ({exc})"
            )
        except GitError as exc:
            return TaskOutcome.failure(message=str(exc))


def all_git_workers() -> list[ExecutableWorker]:
    return [
        GitStatusWorker(),
        GitBranchWorker(),
        GitCommitWorker(),
        GitFetchWorker(),
        GitPullWorker(),
        GitPushWorker(),
    ]
