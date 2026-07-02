"""Vedaws subprocess orchestration (§1.6, §6)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from vespawd_bridge import codes
from vespawd_bridge.cli.allowlist import validate_argv
from vespawd_bridge.cli.parse import VedawsSnapshot, merge_snapshots, parse_artifacts, parse_doctor, parse_state, parse_status_output, parse_workflow_show
from vespawd_bridge.logging.logger import BridgeLogger
from vespawd_bridge.manifest.model import ManifestModel

DEFAULT_TIMEOUTS: dict[str, int] = {
    "version": 10,
    "status": 30,
    "workflow": 30,
    "state": 30,
    "doctor": 120,
    "init": 180,
    "run": 300,
    "tasks": 30,
    "software": 120,
}


@dataclass
class CliResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    argv: list[str] | None = None


class CliAdapter:
    def __init__(
        self,
        manifest: ManifestModel,
        vedaws_project_root: Path,
        logger: BridgeLogger,
        commands_run: list[str],
    ) -> None:
        self.manifest = manifest
        self.vedaws_project_root = vedaws_project_root
        self.logger = logger
        self.commands_run = commands_run
        self._executable, self._extra_env = self._resolve_executable()

    def _resolve_executable(self) -> tuple[list[str], dict[str, str]]:
        cli_value = self.manifest.cli
        path = Path(cli_value)
        workspace = self.vedaws_project_root.parent
        if path.is_absolute() and (path / "pyproject.toml").is_file():
            runtime = path / "runtime"
            return (
                [sys.executable, "-m", "vedaws"],
                {"PYTHONPATH": str(runtime)},
            )
        candidate = (self.vedaws_project_root / cli_value).resolve()
        if candidate.is_dir() and (candidate / "pyproject.toml").is_file():
            runtime = candidate / "runtime"
            return (
                [sys.executable, "-m", "vedaws"],
                {"PYTHONPATH": str(runtime)},
            )
        candidate = (workspace / cli_value).resolve()
        if candidate.is_dir() and (candidate / "pyproject.toml").is_file():
            runtime = candidate / "runtime"
            return (
                [sys.executable, "-m", "vedaws"],
                {"PYTHONPATH": str(runtime)},
            )
        if shutil.which(cli_value):
            return ([cli_value], {})
        return ([cli_value], {})

    def ping(self) -> CliResult:
        return self.run(["version"])

    def _timeout_for(self, argv: list[str]) -> int:
        root = argv[0] if argv else "version"
        if root == "run":
            return DEFAULT_TIMEOUTS["run"]
        if root == "init":
            return DEFAULT_TIMEOUTS["init"]
        if root == "doctor":
            return DEFAULT_TIMEOUTS["doctor"]
        if root == "software":
            return DEFAULT_TIMEOUTS["software"]
        return DEFAULT_TIMEOUTS.get(root, 30)

    def run(self, argv: list[str], *, include_path: bool = True) -> CliResult:
        if not validate_argv(argv):
            raise ValueError(f"CLI command not allowlisted: {argv}")

        full_argv = list(self._executable)
        full_argv.extend(argv)
        if include_path and argv and argv[0] != "version":
            if "--path" not in full_argv:
                if argv[0] == "init":
                    full_argv.extend(["--template", "software", str(self.vedaws_project_root)])
                elif argv[0] == "version":
                    pass
                else:
                    full_argv.extend(["--path", str(self.vedaws_project_root)])

        audit = " ".join(full_argv)
        self.commands_run.append(audit)
        self.logger.cli_invoke(full_argv)

        env = os.environ.copy()
        env.update(self._extra_env)
        timeout = self._timeout_for(argv)
        start = time.perf_counter()

        retries = 0
        max_timeout_retries = 0 if argv[0] == "doctor" else 1
        max_spawn_retries = 0 if argv[0] == "doctor" else 2
        last_result: CliResult | None = None

        attempt_limit = max(max_timeout_retries, max_spawn_retries)
        while retries <= attempt_limit:
            try:
                completed = subprocess.run(
                    full_argv,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    env=env,
                    cwd=str(self.vedaws_project_root),
                )
                duration_ms = int((time.perf_counter() - start) * 1000)
                self.logger.cli_complete(completed.returncode, duration_ms)
                last_result = CliResult(
                    exit_code=completed.returncode,
                    stdout=completed.stdout or "",
                    stderr=completed.stderr or "",
                    timed_out=False,
                    argv=full_argv,
                )
                return last_result
            except subprocess.TimeoutExpired as exc:
                duration_ms = int((time.perf_counter() - start) * 1000)
                self.logger.cli_complete(-1, duration_ms)
                if retries < max_timeout_retries:
                    retries += 1
                    self.logger.warn("cli timeout retry", code=codes.RECOVERY_RETRY)
                    continue
                stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
                stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
                return CliResult(
                    exit_code=-1,
                    stdout=stdout,
                    stderr=stderr or "cli_timeout",
                    timed_out=True,
                    argv=full_argv,
                )
            except OSError as exc:
                if retries < max_spawn_retries:
                    retries += 1
                    time.sleep(0.1 if retries == 1 else 0.5)
                    self.logger.warn("cli spawn retry", code=codes.RECOVERY_RETRY)
                    continue
                return CliResult(
                    exit_code=-1,
                    stdout="",
                    stderr=str(exc),
                    timed_out=False,
                    argv=full_argv,
                )
        assert last_result is not None
        return last_result

    def cli_result_code(self, result: CliResult, *, doctor_strict: bool = False) -> str:
        if result.timed_out:
            return codes.CLI_TIMEOUT
        if result.exit_code == -1 and "vedaws" in result.stderr.lower():
            return codes.VEDAWS_MISSING
        if result.exit_code == -1:
            return codes.CLI_SPAWN_ERROR
        if result.exit_code == 0:
            return codes.CLI_OK
        if doctor_strict and result.argv and "doctor" in result.argv:
            return codes.DOCTOR_BLOCKED
        return codes.CLI_FAILED

    def init_software_template(self, name: str | None) -> CliResult:
        argv = ["init", "--template", "software", str(self.vedaws_project_root)]
        if name:
            argv.extend(["--name", name])
        return self.run(argv, include_path=False)

    def workflow_show(self, workflow_id: str | None = None) -> CliResult:
        wf = workflow_id or self.manifest.workflow_id
        return self.run(["workflow", "show", wf])

    def workflow_activate(self, workflow_id: str | None = None) -> CliResult:
        wf = workflow_id or self.manifest.workflow_id
        return self.run(["workflow", "activate", wf])

    def doctor(self) -> CliResult:
        return self.run(["doctor"])

    def status(self) -> CliResult:
        return self.run(["status"])

    def state(self) -> CliResult:
        return self.run(["state"])

    def state_transition(self, target: str) -> CliResult:
        return self.run(["state", "transition", target])

    def state_history(self) -> CliResult:
        return self.run(["state", "history"])

    def run_dispatch(self) -> CliResult:
        return self.run(["run"])

    def tasks_complete(self, task_ref: str) -> CliResult:
        return self.run(["tasks", "complete", task_ref])

    def tasks_fail(self, task_ref: str) -> CliResult:
        return self.run(["tasks", "fail", task_ref])

    def tasks_show(self, task_ref: str) -> CliResult:
        return self.run(["tasks", "show", task_ref])

    def software_artifacts(self) -> CliResult:
        return self.run(["software", "artifacts"])

    def build_snapshot(
        self,
        *,
        include_doctor: bool = False,
        include_artifacts: bool = False,
    ) -> tuple[VedawsSnapshot, list[str]]:
        issues: list[str] = []
        parts: list[VedawsSnapshot] = []

        status_result = self.status()
        if status_result.exit_code == 0:
            snap = parse_status_output(status_result.stdout)
            snap.raw_outputs["status"] = status_result.stdout
            parts.append(snap)
        else:
            issues.append(self.cli_result_code(status_result))

        wf_result = self.workflow_show()
        if wf_result.exit_code == 0:
            snap = parse_workflow_show(wf_result.stdout, self.manifest.workflow_id)
            snap.raw_outputs["workflow_show"] = wf_result.stdout
            parts.append(snap)
        else:
            issues.append(self.cli_result_code(wf_result))

        state_result = self.state()
        if state_result.exit_code == 0:
            snap = parse_state(state_result.stdout)
            parts.append(snap)

        if include_doctor:
            doctor_result = self.doctor()
            parts.append(
                parse_doctor(doctor_result.stdout, doctor_result.stderr, doctor_result.exit_code)
            )

        if include_artifacts:
            art_result = self.software_artifacts()
            parts.append(
                parse_artifacts(art_result.stdout, art_result.stderr, art_result.exit_code)
            )

        return merge_snapshots(*parts), issues
