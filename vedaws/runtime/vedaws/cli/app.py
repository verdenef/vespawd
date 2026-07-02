"""Vedaws CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vedaws.cli import commands
from vedaws.cli.ai_commands import register_ai_commands
from vedaws.cli.automation_commands import register_automation_commands
from vedaws.cli.plugin_commands import register_plugin_command_parsers


def build_parser(workspace: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vedaws",
        description="Vedaws — Development Operating System",
        epilog=(
            "Examples:\n"
            "  vedaws init --name my-project\n"
            "  vedaws status --path /path/to/workspace\n"
            "  vedaws workflow activate default --path /path/to/workspace\n"
            "  vedaws run --path /path/to/workspace\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    commands.register_commands(subparsers)
    register_automation_commands(subparsers)
    register_ai_commands(subparsers)
    register_plugin_command_parsers(subparsers, workspace)
    return parser


def main(argv: list[str] | None = None) -> int:
    workspace = _workspace_from_argv(argv)
    parser = build_parser(workspace)
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args))


def _workspace_from_argv(argv: list[str] | None) -> Path:
    if not argv:
        return Path.cwd()
    for index, token in enumerate(argv):
        if token in {"-C", "--path"} and index + 1 < len(argv):
            return Path(argv[index + 1]).resolve()
        if token.startswith("--path="):
            return Path(token.split("=", 1)[1]).resolve()
    return Path.cwd()


if __name__ == "__main__":
    raise SystemExit(main())
