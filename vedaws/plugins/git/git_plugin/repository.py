"""Git repository operations via the git CLI."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from git_plugin.errors import (
    DetachedHeadError,
    GitAuthError,
    GitCommandError,
    GitNotInstalledError,
    MergeConflictError,
    NotARepositoryError,
)


@dataclass(frozen=True)
class RepositoryStatus:
    branch: str | None
    detached: bool
    clean: bool
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    untracked: tuple[str, ...]

    @property
    def summary(self) -> str:
        if self.detached:
            head = self.branch or "unknown"
            return f"HEAD detached at {head}"
        branch = self.branch or "(no branch)"
        if self.clean:
            return f"On branch {branch}\nnothing to commit, working tree clean"
        lines = [f"On branch {branch}"]
        if self.staged:
            lines.append(f"Staged: {len(self.staged)} file(s)")
        if self.unstaged:
            lines.append(f"Modified: {len(self.unstaged)} file(s)")
        if self.untracked:
            lines.append(f"Untracked: {len(self.untracked)} file(s)")
        return "\n".join(lines)


def find_git_executable() -> str:
    git = shutil.which("git")
    if git is None:
        raise GitNotInstalledError(
            "Git is not installed or not on PATH — install Git to use the Git plugin"
        )
    return git


def is_git_installed() -> bool:
    return shutil.which("git") is not None


class GitRepository:
    """Thin wrapper around git CLI commands for a repository root."""

    def __init__(self, path: Path, *, git_executable: str | None = None) -> None:
        self.path = path.resolve()
        self.git = git_executable or find_git_executable()

    @classmethod
    def open(cls, path: Path) -> GitRepository:
        repo = cls(path)
        if not repo.is_repository():
            raise NotARepositoryError(
                f"Not a git repository: {repo.path} — run `git init` or use a project inside a repository"
            )
        return repo

    def is_repository(self) -> bool:
        result = self._run(
            ["rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"

    def current_branch(self) -> str | None:
        self._reject_detached_for_branch_ops(allow_show=True)
        result = self._run(["branch", "--show-current"], check=False, capture_output=True)
        branch = result.stdout.strip()
        return branch or None

    def is_detached_head(self) -> bool:
        result = self._run(["symbolic-ref", "-q", "HEAD"], check=False, capture_output=True)
        return result.returncode != 0

    def status(self) -> RepositoryStatus:
        branch = self._resolve_head_label()
        porcelain = self._run(["status", "--porcelain"], capture_output=True).stdout
        staged: list[str] = []
        unstaged: list[str] = []
        untracked: list[str] = []
        for line in porcelain.splitlines():
            if len(line) < 4:
                continue
            index_status = line[0]
            worktree_status = line[1]
            path = line[3:]
            if index_status == "?" and worktree_status == "?":
                untracked.append(path)
            else:
                if index_status not in {" ", "?"}:
                    staged.append(path)
                if worktree_status not in {" ", "?"}:
                    unstaged.append(path)
        clean = not staged and not unstaged and not untracked
        return RepositoryStatus(
            branch=branch,
            detached=self.is_detached_head(),
            clean=clean,
            staged=tuple(staged),
            unstaged=tuple(unstaged),
            untracked=tuple(untracked),
        )

    def create_branch(self, name: str) -> str:
        if self.is_detached_head():
            raise DetachedHeadError(
                "Cannot create branch while in detached HEAD state — checkout a branch first"
            )
        self._run(["checkout", "-b", name], capture_output=True)
        return name

    def stage(self, paths: list[str] | None = None) -> None:
        if paths:
            self._run(["add", "--", *paths], capture_output=True)
        else:
            self._run(["add", "-A"], capture_output=True)

    def commit(self, message: str) -> str:
        if self.is_detached_head():
            raise DetachedHeadError(
                "Cannot commit on detached HEAD — checkout a branch first"
            )
        result = self._run(["commit", "-m", message], capture_output=True)
        return result.stdout.strip() or "Commit created"

    def fetch(self, remote: str = "origin") -> str:
        result = self._run(["fetch", remote], capture_output=True)
        return result.stdout.strip() or f"Fetched from {remote}"

    def pull(self, remote: str = "origin") -> str:
        result = self._run(["pull", remote], check=False, capture_output=True)
        if result.returncode != 0:
            self._raise_pull_error(result)
        return result.stdout.strip() or f"Pulled from {remote}"

    def push(self, remote: str = "origin") -> str:
        result = self._run(["push", remote], check=False, capture_output=True)
        if result.returncode != 0:
            self._raise_push_error(result)
        return result.stdout.strip() or f"Pushed to {remote}"

    def _resolve_head_label(self) -> str | None:
        branch = self._run(["branch", "--show-current"], check=False, capture_output=True)
        if branch.stdout.strip():
            return branch.stdout.strip()
        detached = self._run(
            ["rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
        )
        return detached.stdout.strip() or None

    def _reject_detached_for_branch_ops(self, *, allow_show: bool = False) -> None:
        if not allow_show and self.is_detached_head():
            raise DetachedHeadError(
                "HEAD is detached — checkout a branch before this operation"
            )

    def _raise_pull_error(self, result: subprocess.CompletedProcess[str]) -> None:
        combined = f"{result.stdout}\n{result.stderr}".lower()
        if "conflict" in combined or self._has_merge_conflicts():
            raise MergeConflictError(
                "Merge conflicts detected — resolve conflicts before continuing"
            )
        raise GitCommandError(["pull"], result.returncode, result.stderr)

    def _raise_push_error(self, result: subprocess.CompletedProcess[str]) -> None:
        combined = f"{result.stderr}\n{result.stdout}".lower()
        auth_markers = (
            "authentication failed",
            "could not read username",
            "permission denied",
            "invalid credentials",
            "support for password authentication was removed",
            "terminal prompts disabled",
        )
        if any(marker in combined for marker in auth_markers):
            raise GitAuthError(
                "Push requires authentication — configure credentials or use SSH remotes"
            )
        raise GitCommandError(["push"], result.returncode, result.stderr)

    def _has_merge_conflicts(self) -> bool:
        status = self._run(["status", "--porcelain"], capture_output=True).stdout
        for line in status.splitlines():
            if len(line) >= 2 and line[0] in {"U", "A"} and line[1] in {"U", "A"}:
                return True
            if line.startswith("UU "):
                return True
        return False

    def _run(
        self,
        args: list[str],
        *,
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = [self.git, *args]
        try:
            result = subprocess.run(
                command,
                cwd=self.path,
                check=False,
                capture_output=capture_output,
                text=True,
            )
        except OSError as exc:
            raise GitNotInstalledError(
                "Git is not installed or not on PATH — install Git to use the Git plugin"
            ) from exc
        if check and result.returncode != 0:
            raise GitCommandError(command, result.returncode, result.stderr)
        return result
