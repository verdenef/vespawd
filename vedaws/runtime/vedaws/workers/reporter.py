"""Worker listing output for CLI."""

from __future__ import annotations

from vedaws.runtime.context import RuntimeContext
from vedaws.workers.registry import WorkerRegistry


def format_workers(registry: WorkerRegistry) -> str:
    workers = registry.list_workers()
    if not workers:
        return "No workers registered."

    lines = [
        f"{'ID':<24} {'TYPE':<8} {'VERSION':<10} {'STATUS':<12} {'EXEC':<8} CAPABILITIES",
        "-" * 90,
    ]
    for worker in workers:
        capabilities = ", ".join(worker.metadata.capability_labels) or "(none)"
        if worker.is_executable:
            executable = "runtime"
        else:
            executable = "manifest"
        lines.append(
            f"{worker.id:<24} {worker.metadata.worker_type.value:<8} "
            f"{worker.metadata.version:<10} {str(worker.status):<12} {executable:<8} {capabilities}"
        )
    lines.append("")
    lines.append(f"Total: {registry.count} worker(s)")
    return "\n".join(lines)


def format_workers_from_context(context: RuntimeContext) -> str:
    return format_workers(context.worker_registry)
