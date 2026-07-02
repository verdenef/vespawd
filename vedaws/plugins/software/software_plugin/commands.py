"""CLI commands for the Software Workflow plugin."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from software_plugin.artifacts import (
    SOFTWARE_WORKFLOW_ID,
    format_artifact_report,
    list_artifact_status,
)
from vedaws.runtime.bootstrap import bootstrap
from vedaws.workflow.reporter import format_workflow_detail


def cmd_status(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=True)
    if context.project is None:
        print("error: no Vedaws project — run `vedaws init --template software`", file=sys.stderr)
        return 1

    print(f"Project: {context.project.name}")
    print(f"State:   {context.project.state_name}")
    print()
    print(format_artifact_report(workspace))

    if context.project.workflow_engine is not None:
        try:
            print()
            print(format_workflow_detail(context.project.workflow_engine, SOFTWARE_WORKFLOW_ID))
        except Exception:  # noqa: BLE001
            print(f"\nWorkflow '{SOFTWARE_WORKFLOW_ID}' not loaded yet.")
    return 0


def cmd_artifacts(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    if not (workspace / ".vedaws").is_dir():
        print("error: no Vedaws project in workspace", file=sys.stderr)
        return 1
    print(format_artifact_report(workspace))
    missing = [status for status in list_artifact_status(workspace) if not status.exists]
    return 1 if missing else 0


def cmd_workflow(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=True)
    if context.project is None or context.project.workflow_engine is None:
        print("error: workflow engine not available", file=sys.stderr)
        return 1
    print(format_workflow_detail(context.project.workflow_engine, SOFTWARE_WORKFLOW_ID))
    return 0
