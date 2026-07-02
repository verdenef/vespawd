"""Automation CLI command implementations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vedaws.automation.config import load_automation_config, save_rule_override
from vedaws.automation.reporter import format_execution_results, format_rule_list
from vedaws.events.model import create_event
from vedaws.runtime.bootstrap import bootstrap


def _load_automation_context(args: argparse.Namespace):
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)
    if context.automation_engine is None:
        print("Automation engine not available.", file=sys.stderr)
        return None
    return context


def cmd_automation(args: argparse.Namespace) -> int:
    command = getattr(args, "automation_command", None)

    if command == "enable":
        workspace = Path(args.path).resolve()
        try:
            path = save_rule_override(workspace, args.rule_id, enabled=True)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Enabled automation rule '{args.rule_id}' ({path})")
        return 0

    if command == "disable":
        workspace = Path(args.path).resolve()
        try:
            path = save_rule_override(workspace, args.rule_id, enabled=False)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Disabled automation rule '{args.rule_id}' ({path})")
        return 0

    if command == "run":
        context = _load_automation_context(args)
        if context is None:
            return 1
        engine = context.automation_engine
        if engine is None:
            return 1

        if args.rule_id:
            event = _event_from_args(args) if args.event_type else None
            result = engine.run_rule(args.rule_id, event)
            print(format_execution_results([result]))
            return 0 if result.success else 1

        if args.event_type:
            event = _event_from_args(args)
            results = engine.run_for_event(event)
            print(format_execution_results(results))
            return 0 if all(result.success or result.skipped for result in results) else 1

        print("error: specify --rule or --event", file=sys.stderr)
        return 1

    context = _load_automation_context(args)
    if context is None:
        return 1
    engine = context.automation_engine
    if engine is None:
        return 1
    config = load_automation_config(context.workspace)
    print(format_rule_list(engine.registry))
    if not config.enabled:
        print()
        print("Project automation is globally disabled in .vedaws/automation.toml")
    return 0


def _event_from_args(args: argparse.Namespace):
    payload: dict[str, str] = {}
    for item in getattr(args, "payload", []) or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        payload[key.strip()] = value.strip()
    return create_event(
        args.event_type,
        source="automation-cli",
        payload=payload,
    )


def register_automation_commands(subparsers: argparse._SubParsersAction) -> None:
    automation_args = argparse.ArgumentParser(add_help=False)
    automation_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    automation_args.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    automation_parser = subparsers.add_parser(
        "automation",
        parents=[automation_args],
        help="List and manage automation rules",
    )
    automation_subparsers = automation_parser.add_subparsers(dest="automation_command")

    list_parser = automation_subparsers.add_parser(
        "list",
        parents=[automation_args],
        help="List automation rules",
    )
    list_parser.set_defaults(automation_command="list")

    enable_parser = automation_subparsers.add_parser(
        "enable",
        parents=[automation_args],
        help="Enable an automation rule",
    )
    enable_parser.add_argument("rule_id", help="Rule id")
    enable_parser.set_defaults(automation_command="enable")

    disable_parser = automation_subparsers.add_parser(
        "disable",
        parents=[automation_args],
        help="Disable an automation rule",
    )
    disable_parser.add_argument("rule_id", help="Rule id")
    disable_parser.set_defaults(automation_command="disable")

    run_parser = automation_subparsers.add_parser(
        "run",
        parents=[automation_args],
        help="Manually run automation rule(s)",
    )
    run_parser.add_argument("--rule", dest="rule_id", help="Run a specific rule by id")
    run_parser.add_argument("--event", dest="event_type", help="Synthetic event type")
    run_parser.add_argument(
        "--payload",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Payload field for synthetic event (repeatable)",
    )
    run_parser.set_defaults(automation_command="run")

    automation_parser.set_defaults(handler=cmd_automation, automation_command=None)
