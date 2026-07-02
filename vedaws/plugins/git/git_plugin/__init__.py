"""Git plugin — first-party reference implementation."""

from __future__ import annotations

from pathlib import Path

from git_plugin import commands
from git_plugin.repository import GitRepository, find_git_executable, is_git_installed
from git_plugin.workers import all_git_workers
from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.plugins.sdk import PluginContext, VedawsPlugin


class GitPlugin(VedawsPlugin):
    """Production-quality Git integration via the Vedaws plugin SDK."""

    def register(self, context: PluginContext) -> None:
        for worker in all_git_workers():
            context.contribute_worker(worker)

        context.contribute_health_check(self._check_git_installed)
        context.contribute_health_check(self._check_git_plugin_loaded)
        context.contribute_health_check(self._check_git_workers)
        context.contribute_health_check(self._check_git_repository)

        context.contribute_command(
            "status",
            "Show repository status",
            group="git",
            handler=commands.cmd_status,
        )
        context.contribute_command(
            "branch",
            "Show or create the current branch",
            group="git",
            handler=commands.cmd_branch,
        )
        context.contribute_command(
            "commit",
            "Stage and commit changes",
            group="git",
            handler=commands.cmd_commit,
        )
        context.contribute_command(
            "fetch",
            "Fetch from a remote",
            group="git",
            handler=commands.cmd_fetch,
        )
        context.contribute_command(
            "pull",
            "Pull from a remote",
            group="git",
            handler=commands.cmd_pull,
        )
        context.contribute_command(
            "push",
            "Push to a remote",
            group="git",
            handler=commands.cmd_push,
        )

        context.contribute_configuration(
            {
                "git": {
                    "default_remote": {
                        "type": "string",
                        "default": "origin",
                        "description": "Default remote for fetch, pull, and push",
                    }
                }
            }
        )

    def _check_git_installed(self) -> HealthCheckResult:
        if is_git_installed():
            return HealthCheckResult(
                "git installation",
                CheckStatus.PASS,
                f"Git executable found at {find_git_executable()}",
            )
        return HealthCheckResult(
            "git installation",
            CheckStatus.FAIL,
            "Git is not installed or not on PATH",
        )

    def _check_git_plugin_loaded(self) -> HealthCheckResult:
        return HealthCheckResult(
            "git plugin",
            CheckStatus.PASS,
            "Git plugin loaded and active",
        )

    def _check_git_workers(self) -> HealthCheckResult:
        worker_ids = [worker.id for worker in all_git_workers()]
        return HealthCheckResult(
            "git workers",
            CheckStatus.PASS,
            f"{len(worker_ids)} Git worker(s) registered: {', '.join(worker_ids)}",
        )

    def _check_git_repository(self) -> HealthCheckResult:
        workspace = Path.cwd()
        if not is_git_installed():
            return HealthCheckResult(
                "git repository",
                CheckStatus.WARN,
                "Cannot detect repository — Git is not installed",
            )
        repo = GitRepository(workspace)
        if repo.is_repository():
            status = repo.status()
            branch = status.branch or "(detached)"
            return HealthCheckResult(
                "git repository",
                CheckStatus.PASS,
                f"Git repository detected at {workspace} — {branch}",
            )
        return HealthCheckResult(
            "git repository",
            CheckStatus.WARN,
            f"No git repository at {workspace}",
        )
