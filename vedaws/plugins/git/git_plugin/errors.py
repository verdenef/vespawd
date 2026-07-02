"""Git plugin errors."""

from __future__ import annotations


class GitError(Exception):
    """Base error for Git plugin operations."""


class GitNotInstalledError(GitError):
    """Raised when the git executable is not available."""


class NotARepositoryError(GitError):
    """Raised when the workspace is not inside a Git repository."""


class DetachedHeadError(GitError):
    """Raised when an operation requires a named branch but HEAD is detached."""


class MergeConflictError(GitError):
    """Raised when merge or pull results in conflicts."""


class GitAuthError(GitError):
    """Raised when authentication is required but unavailable."""


class GitCommandError(GitError):
    """Raised when a git command fails."""

    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr.strip()
        message = self.stderr or f"git command failed with exit code {returncode}"
        super().__init__(message)
