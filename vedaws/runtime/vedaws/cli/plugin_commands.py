"""Dynamic CLI registration for plugin-contributed commands."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from vedaws.plugins.commands import collect_plugin_command_groups


def register_plugin_command_parsers(
    subparsers: argparse._SubParsersAction,
    workspace: Path | None = None,
) -> None:
    """Register argparse parsers for all active plugin command groups."""
    try:
        groups = collect_plugin_command_groups(workspace)
    except Exception:  # noqa: BLE001 — parser build must not fail on plugin errors
        return

    for group in groups:
        if len(group.commands) == 1 and group.commands[0].group is None:
            _register_top_level_command(subparsers, group.commands[0])
            continue
        _register_command_group(subparsers, group)


def _register_top_level_command(
    subparsers: argparse._SubParsersAction,
    command,
) -> None:
    parser = subparsers.add_parser(
        command.name,
        help=command.description,
        parents=[_plugin_args_parser()],
    )
    parser.set_defaults(handler=_wrap_handler(command.handler))


def _register_command_group(subparsers: argparse._SubParsersAction, group) -> None:
    group_parser = subparsers.add_parser(
        group.name,
        help=group.description or f"Plugin commands: {group.name}",
        parents=[_plugin_args_parser()],
    )
    group_subparsers = group_parser.add_subparsers(
        dest="plugin_subcommand",
        required=True,
    )
    for command in group.commands:
        if command.group != group.name:
            continue
        subparser = group_subparsers.add_parser(
            command.name,
            help=command.description,
            parents=[_plugin_args_parser()],
        )
        _add_command_arguments(subparser, command.name)
        subparser.set_defaults(handler=_wrap_handler(command.handler))


def _plugin_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    return parser


def _add_command_arguments(parser: argparse.ArgumentParser, command_name: str) -> None:
    if command_name == "branch":
        parser.add_argument(
            "--create",
            metavar="NAME",
            help="Create and checkout a new branch",
        )
    elif command_name == "commit":
        parser.add_argument("-m", "--message", required=True, help="Commit message")
        parser.add_argument(
            "--stage-all",
            action="store_true",
            help="Stage all changes before committing",
        )
        parser.add_argument(
            "--stage",
            nargs="*",
            default=None,
            metavar="PATH",
            help="Stage specific paths before committing",
        )
    elif command_name in {"fetch", "pull", "push"}:
        parser.add_argument(
            "--remote",
            default="origin",
            help="Remote name (default: origin)",
        )
    elif command_name == "build":
        parser.add_argument(
            "--target",
            default=None,
            help="Build target placeholder (e.g. standalone, android)",
        )


def _wrap_handler(handler: Callable[..., int] | None):
    def dispatch(args: argparse.Namespace) -> int:
        if handler is None:
            print("error: plugin command handler is missing", file=sys.stderr)
            return 1
        return int(handler(args))

    return dispatch
