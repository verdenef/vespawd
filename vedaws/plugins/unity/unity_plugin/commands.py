"""CLI commands for the Unity Game Development plugin."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from unity_plugin.artifacts import (
    UNITY_WORKFLOW_ID,
    format_artifact_report,
    format_layout_report,
    layout_is_valid,
    list_artifact_status,
)
from vedaws.runtime.bootstrap import bootstrap
from vedaws.workflow.reporter import format_workflow_detail


def cmd_status(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=True)
    if context.project is None:
        print("error: no Vedaws project — run `vedaws init unity`", file=sys.stderr)
        return 1

    print(f"Project: {context.project.name}")
    print(f"State:   {context.project.state_name}")
    print()
    print(format_layout_report(workspace))
    print()
    print(format_artifact_report(workspace))

    if context.project.workflow_engine is not None:
        try:
            print()
            print(format_workflow_detail(context.project.workflow_engine, UNITY_WORKFLOW_ID))
        except Exception:  # noqa: BLE001
            print(f"\nWorkflow '{UNITY_WORKFLOW_ID}' not loaded yet.")
    return 0


def cmd_workflow(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=True)
    if context.project is None or context.project.workflow_engine is None:
        print("error: workflow engine not available", file=sys.stderr)
        return 1
    print(format_workflow_detail(context.project.workflow_engine, UNITY_WORKFLOW_ID))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    if not (workspace / ".vedaws").is_dir():
        print("error: no Vedaws project in workspace", file=sys.stderr)
        return 1
    if not layout_is_valid(workspace):
        print("error: Unity project layout is incomplete", file=sys.stderr)
        return 1
    target = args.target or "placeholder"
    print(f"Unity build stub — target={target}")
    print("Unity Editor integration is not available in this milestone.")
    print("Document build output in Docs/builds/ when ready.")
    builds_dir = workspace / "Docs" / "builds"
    builds_dir.mkdir(parents=True, exist_ok=True)
    log_path = builds_dir / "BUILD_LOG.md"
    if not log_path.is_file():
        log_path.write_text(
            "# Build Log\n\nPlaceholder build recorded by `vedaws unity build`.\n",
            encoding="utf-8",
        )
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    if not (workspace / ".vedaws").is_dir():
        print("error: no Vedaws project in workspace", file=sys.stderr)
        return 1
    if not layout_is_valid(workspace):
        print("error: Unity project layout is incomplete", file=sys.stderr)
        return 1
    print("Unity package stub — UPM manifest placeholder only.")
    print("Unity Editor and package publishing are not integrated in this milestone.")
    manifest = workspace / "Packages" / "manifest.json"
    if manifest.is_file():
        print(f"Packages manifest: {manifest}")
    return 0
