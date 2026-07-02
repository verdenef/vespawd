"""Plugin listing and detail formatting for CLI output."""

from __future__ import annotations

from vedaws.plugins.lifecycle import PluginStatus
from vedaws.plugins.registry import PluginRecord, PluginRegistry


def format_plugin_list(registry: PluginRegistry) -> str:
    lines = ["Plugins:", ""]
    records = registry.list_records()
    if not records:
        lines.append("  (none discovered)")
        return "\n".join(lines)

    lines.append(f"  {'ID':<16} {'VERSION':<10} {'STATUS':<12} NAME")
    lines.append(f"  {'-' * 16} {'-' * 10} {'-' * 12} {'-' * 20}")
    for record in records:
        manifest = record.manifest
        lines.append(
            f"  {manifest.id:<16} {manifest.version:<10} {record.status.value:<12} {manifest.display_name}"
        )

    active = registry.active_count
    lines.extend(["", f"Active: {active} / {registry.count} discovered"])
    if registry.discovery and registry.discovery.invalid:
        lines.append(f"Invalid manifests: {len(registry.discovery.invalid)}")
    if registry.discovery and registry.discovery.duplicates:
        lines.append(f"Duplicate ids: {len(registry.discovery.duplicates)}")
    return "\n".join(lines)


def format_plugin_info(record: PluginRecord) -> str:
    manifest = record.manifest
    lines = [
        f"Plugin:      {manifest.id}",
        f"Name:        {manifest.display_name}",
        f"Version:     {manifest.version}",
        f"Status:      {record.status.value}",
        f"Author:      {manifest.author or '(not specified)'}",
        f"Description: {manifest.description or '(none)'}",
        f"Entry point: {manifest.entry_point}",
    ]
    if manifest.manifest_path is not None:
        lines.append(f"Manifest:    {manifest.manifest_path}")
    if record.error:
        lines.append(f"Error:       {record.error}")

    lines.extend(["", "Compatibility:"])
    lines.append(f"  Vedaws:  {manifest.compatibility.vedaws}")
    lines.append(f"  Python:  {manifest.compatibility.python}")

    if manifest.dependencies:
        lines.extend(["", "Dependencies:"])
        for dep in manifest.dependencies:
            lines.append(f"  - {dep.id} {dep.version}")

    caps = manifest.capabilities
    cap_labels = [
        label
        for label, enabled in (
            ("workers", caps.workers),
            ("commands", caps.commands),
            ("workflows", caps.workflows),
            ("projects", caps.projects),
            ("skills", caps.skills),
            ("health_checks", caps.health_checks),
            ("configuration", caps.configuration),
        )
        if enabled
    ]
    lines.extend(
        ["", f"Capabilities: {', '.join(cap_labels) if cap_labels else '(none declared)'}"]
    )

    if record.contributions is not None:
        contrib = record.contributions
        lines.extend(
            [
                "",
                "Contributions:",
                f"  Workers:            {len(contrib.workers)}",
                f"  Commands:           {len(contrib.commands)}",
                f"  Workflow templates: {len(contrib.workflow_templates)}",
                f"  Project templates:  {len(contrib.project_templates)}",
                f"  Skills:             {len(contrib.skills)}",
                f"  Health checks:      {len(contrib.health_checks)}",
                f"  Configuration keys: {len(contrib.configuration)}",
            ]
        )
        if contrib.workers:
            lines.append("")
            lines.append("  Worker ids:")
            for worker in contrib.workers:
                lines.append(f"    - {worker.id}")

    return "\n".join(lines)


def format_plugin_summary(registry: PluginRegistry) -> list[str]:
    """Return status lines for the runtime status reporter."""
    records = registry.list_records()
    if not records:
        return ["  (none discovered)"]
    lines: list[str] = []
    for record in records:
        suffix = ""
        if record.status == PluginStatus.ACTIVE:
            suffix = " [active]"
        elif record.status == PluginStatus.FAILED:
            suffix = " [failed]"
        elif record.status == PluginStatus.DISABLED:
            suffix = " [disabled]"
        lines.append(
            f"  - {record.manifest.id} ({record.manifest.version}) "
            f"— {record.manifest.display_name}{suffix}"
        )
    return lines
