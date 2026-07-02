"""Runtime status reporting."""

from __future__ import annotations

from vedaws.plugins.reporter import format_plugin_summary
from vedaws.runtime.context import RuntimeContext


def format_status(context: RuntimeContext) -> str:
    lines = [
        f"Vedaws version:   {context.version}",
        f"Runtime status:   {context.status}",
        f"Runtime name:     {context.config.runtime.name}",
        f"Workspace:        {context.workspace}",
        "",
        "Plugins:",
    ]

    lines.extend(format_plugin_summary(context.registry))

    lines.extend(["", "Workers:"])
    workers = context.worker_registry.list_workers()
    if not workers:
        lines.append("  (none registered)")
    else:
        for worker in workers:
            caps = ", ".join(worker.metadata.capability_labels)
            lines.append(
                f"  - {worker.id} [{worker.metadata.worker_type.value}] "
                f"({worker.metadata.version}) — {caps}"
            )

    lines.extend(["", "Current project:"])
    if context.project is None:
        lines.append("  (none — run `vedaws init` in a workspace)")
        lines.append("")
        lines.append("Project state:    (none)")
    else:
        lines.append(f"  {context.project.name}")
        lines.append(f"  {context.project.root}")
        lines.append("")
        lines.append(f"Project state:    {context.project.state_name}")
        if context.project.workflow_engine is not None:
            workflows = context.project.workflow_engine.list_workflows()
            active = sum(
                1
                for workflow in workflows
                if context.project.workflow_engine.progress(workflow.id).status.value
                not in {"defined", "cancelled"}
            )
            lines.append(f"Workflows:        {len(workflows)} defined, {active} active")
            ready = len(context.project.workflow_engine.task_registry.list_ready())
            lines.append(f"Ready tasks:      {ready}")
        if context.dispatcher is not None:
            lines.append(f"Dispatcher:       ready ({len(context.worker_registry.list_executable())} executable workers)")

    return "\n".join(lines)
