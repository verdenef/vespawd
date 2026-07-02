"""CLI command handlers for the Git plugin."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from git_plugin.errors import (
    DetachedHeadError,
    GitAuthError,
    GitError,
    GitNotInstalledError,
    MergeConflictError,
    NotARepositoryError,
)
from git_plugin.repository import GitRepository


def cmd_status(args: argparse.Namespace) -> int:
    return _run_repo_command(args, lambda repo: _print(repo.status().summary))


def cmd_branch(args: argparse.Namespace) -> int:
    def action(repo: GitRepository) -> None:
        if args.create:
            name = repo.create_branch(args.create)
            print(f"Created and checked out branch '{name}'")
            return
        status = repo.status()
        if status.detached:
            print(f"HEAD detached at {status.branch or 'unknown'}")
            return
        branch = repo.current_branch()
        print(branch or "(no branch)")

    return _run_repo_command(args, action)


def cmd_commit(args: argparse.Namespace) -> int:
    def action(repo: GitRepository) -> None:
        if args.stage_all:
            repo.stage()
        elif args.stage:
            repo.stage(list(args.stage))
        message = repo.commit(args.message)
        print(message)

    return _run_repo_command(args, action)


def cmd_fetch(args: argparse.Namespace) -> int:
    return _run_repo_command(
        args,
        lambda repo: print(repo.fetch(remote=args.remote)),
    )


def cmd_pull(args: argparse.Namespace) -> int:
    return _run_repo_command(
        args,
        lambda repo: print(repo.pull(remote=args.remote)),
    )


def cmd_push(args: argparse.Namespace) -> int:
    def action(repo: GitRepository) -> None:
        try:
            print(repo.push(remote=args.remote))
        except GitAuthError as exc:
            print(f"warning: {exc}", file=sys.stderr)
            print("Push skipped — authentication not available in this environment")

    return _run_repo_command(args, action, auth_exit_code=0)


def _run_repo_command(
    args: argparse.Namespace,
    action,
    *,
    auth_exit_code: int | None = None,
) -> int:
    workspace = Path(args.path).resolve()
    try:
        repo = GitRepository.open(workspace)
        action(repo)
        return 0
    except GitNotInstalledError as exc:
        return _fail(str(exc))
    except NotARepositoryError as exc:
        return _fail(str(exc))
    except DetachedHeadError as exc:
        return _fail(str(exc))
    except MergeConflictError as exc:
        return _fail(str(exc))
    except GitAuthError as exc:
        if auth_exit_code is not None:
            print(f"warning: {exc}", file=sys.stderr)
            return auth_exit_code
        return _fail(str(exc))
    except GitError as exc:
        return _fail(str(exc))


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def _print(message: str) -> None:
    print(message)
