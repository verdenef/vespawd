"""AI CLI commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vedaws.ai.reporter import format_ai_status, format_capability_map, format_provider_list
from vedaws.ai.validator import validate_ai_platform
from vedaws.runtime.bootstrap import bootstrap


def cmd_ai(args: argparse.Namespace) -> int:
    command = getattr(args, "ai_command", None)
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)
    service = context.ai_service
    if service is None:
        print("AI service not available.", file=sys.stderr)
        return 1

    if command == "providers":
        print(format_provider_list(service))
        return 0

    if command == "capabilities":
        print(format_capability_map(service))
        return 0

    if command == "status":
        validation = validate_ai_platform(service.registry, service.router.config)
        print(
            format_ai_status(
                service,
                service.provider_health(),
                validation,
            )
        )
        return 0 if validation.ok else 1

    print(format_provider_list(service))
    return 0


def register_ai_commands(subparsers: argparse._SubParsersAction) -> None:
    ai_args = argparse.ArgumentParser(add_help=False)
    ai_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    ai_args.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    ai_parser = subparsers.add_parser(
        "ai",
        parents=[ai_args],
        help="AI provider platform",
    )
    ai_subparsers = ai_parser.add_subparsers(dest="ai_command")

    providers_parser = ai_subparsers.add_parser(
        "providers",
        parents=[ai_args],
        help="List registered AI providers",
    )
    providers_parser.set_defaults(ai_command="providers")

    capabilities_parser = ai_subparsers.add_parser(
        "capabilities",
        parents=[ai_args],
        help="List AI capabilities and routing",
    )
    capabilities_parser.set_defaults(ai_command="capabilities")

    status_parser = ai_subparsers.add_parser(
        "status",
        parents=[ai_args],
        help="Show AI platform status and validation",
    )
    status_parser.set_defaults(ai_command="status")

    ai_parser.set_defaults(handler=cmd_ai, ai_command=None)
