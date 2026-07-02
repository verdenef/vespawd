"""Plugin command collection for CLI dispatch."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.plugins.contributions import PluginCommand
from vedaws.runtime.bootstrap import bootstrap


@dataclass
class PluginCommandGroup:
    name: str
    description: str
    commands: list[PluginCommand] = field(default_factory=list)


def collect_plugin_command_groups(workspace: Path | None = None) -> list[PluginCommandGroup]:
    """Bootstrap quietly and return command groups contributed by active plugins."""
    workspace = (workspace or Path.cwd()).resolve()
    context = bootstrap(workspace, quiet=True)
    grouped: dict[str, list[PluginCommand]] = defaultdict(list)
    descriptions: dict[str, str] = {}

    for record in context.registry.list_active():
        if record.contributions is None:
            continue
        for command in record.contributions.commands:
            if command.handler is None:
                continue
            group_name = command.group or command.name
            grouped[group_name].append(command)
            if command.group and group_name not in descriptions:
                descriptions[group_name] = f"Commands from plugin '{record.id}'"
            elif not command.group:
                descriptions[group_name] = command.description

    result: list[PluginCommandGroup] = []
    for group_name in sorted(grouped):
        commands = sorted(grouped[group_name], key=lambda cmd: cmd.name)
        result.append(
            PluginCommandGroup(
                name=group_name,
                description=descriptions.get(group_name, ""),
                commands=commands,
            )
        )
    return result
