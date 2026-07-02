"""Project template listing for CLI."""

from __future__ import annotations

from vedaws.project.templates import ProjectTemplate


def format_project_template_list(templates: list[ProjectTemplate]) -> str:
    lines = ["Project templates:", ""]
    if not templates:
        lines.append("  (none discovered — enable plugins that contribute templates)")
        return "\n".join(lines)

    lines.append(f"  {'ID':<14} {'PLUGIN':<12} NAME")
    lines.append(f"  {'-' * 14} {'-' * 12} {'-' * 24}")
    for template in templates:
        plugin = template.plugin_id or "(unknown)"
        lines.append(f"  {template.id:<14} {plugin:<12} {template.name}")
        if template.description:
            lines.append(f"    {template.description}")
    lines.extend(
        [
            "",
            "Usage:",
            "  vedaws init --template <id> [path]",
            "  vedaws init software          # template id shorthand (cwd)",
            "  vedaws init unity             # Unity game template",
            "  vedaws init --list-templates",
        ]
    )
    return "\n".join(lines)
