"""CLI command implementations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vedaws import __version__
from vedaws.doctor.checks import overall_status, run_health_checks
from vedaws.config.loader import load_config
from vedaws.events.integration import publish_project_initialized
from vedaws.project.init import init_project
from vedaws.project.templates import get_project_template
from vedaws.project.template_reporter import format_project_template_list
from vedaws.project.templates import discover_project_templates
from vedaws.project.detector import sync_manifest_state
from vedaws.project.state import ProjectState, TransitionTrigger
from vedaws.project.state.reporter import format_current_state, format_state_history
from vedaws.dispatch.reporter import format_dispatch_result, format_run_summary
from vedaws.dispatch.runner import run_until_idle
from vedaws.runtime.bootstrap import bootstrap
from vedaws.status.reporter import format_status
from vedaws.workflow.engine import WorkflowError, parse_task_ref
from vedaws.workflow.reporter import (
    format_task_detail,
    format_task_list,
    format_workflow_detail,
    format_workflow_list,
)
from vedaws.plugins.activation import (
    disable_plugin,
    enable_plugin,
    global_plugins_path,
    project_plugins_path,
)
from vedaws.plugins.reporter import format_plugin_info, format_plugin_list
from vedaws.events.reporter import format_event_bus_status
from vedaws.workers.reporter import format_workers_from_context


def _resolve_workspace_arg(args: argparse.Namespace) -> Path:
    """Resolve workspace path from shared CLI conventions.

    Most commands support `-C/--path`; a few legacy commands also accept a
    positional path for backward compatibility.
    """
    explicit = getattr(args, "workspace", None)
    if explicit:
        return Path(explicit).resolve()
    positional = getattr(args, "path", None)
    if positional:
        return Path(positional).resolve()
    return Path(".").resolve()


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"vedaws {__version__}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    if args.list_templates:
        workspace = Path.cwd().resolve()
        config = load_config(workspace)
        templates = discover_project_templates(config)
        print(format_project_template_list(templates))
        return 0

    config = load_config(Path.cwd())
    template = None
    workspace = Path(args.path).resolve()

    if args.template:
        template = get_project_template(config, args.template)
        if template is None:
            print(f"error: project template '{args.template}' not found", file=sys.stderr)
            print("Run `vedaws init --list-templates` to list available templates.", file=sys.stderr)
            return 1
    else:
        candidate = get_project_template(config, args.path)
        if candidate is not None and args.path == candidate.id:
            template = candidate
            workspace = Path.cwd().resolve()

    try:
        config_dir = init_project(workspace, name=args.name, template=template)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    context = bootstrap(workspace, quiet=True)
    publish_project_initialized(
        context.event_bus,
        project_name=args.name or workspace.name,
        project_root=str(workspace),
    )
    if template is not None:
        print(f"Initialized Vedaws project at {config_dir}")
        print(f"Template: {template.name} ({template.id})")
        if template.default_workflow:
            print(f"Next: run `vedaws workflow activate {template.default_workflow}`")
    else:
        print(f"Initialized Vedaws project at {config_dir}")
        print("Next: run `vedaws status` to inspect the runtime")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    workspace = _resolve_workspace_arg(args)
    context = bootstrap(workspace, quiet=not args.verbose)
    print(format_status(context))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    workspace = _resolve_workspace_arg(args)
    results = run_health_checks(workspace, quiet=not args.verbose)
    for result in results:
        print(f"[{result.status}] {result.name}: {result.message}")

    summary = overall_status(results)
    print()
    print(f"Overall: {summary}")
    if summary == "FAIL":
        return 1
    if summary == "WARN":
        return 0
    return 0


def cmd_workers(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)

    if getattr(args, "workers_command", None) == "run":
        if context.dispatcher is None:
            print("Dispatcher not available — initialize a project first.", file=sys.stderr)
            return 1
        worker = context.worker_registry.get(args.worker_id)
        if worker is None:
            print(f"error: worker '{args.worker_id}' not found", file=sys.stderr)
            return 1
        if not worker.is_executable:
            print(f"error: worker '{args.worker_id}' cannot execute tasks", file=sys.stderr)
            return 1

        if args.task_ref:
            try:
                workflow_id, task_id = parse_task_ref(args.task_ref)
            except WorkflowError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
        else:
            ready = context.dispatcher.list_ready_tasks()
            match = None
            for task in ready:
                task_def = (
                    context.project.workflow_engine.task_registry.get_definition(
                        task.workflow_id, task.task_id
                    )
                    if context.project and context.project.workflow_engine
                    else None
                )
                if task_def and context.dispatcher.find_worker_for_task(
                    task_def, preferred_worker_id=args.worker_id
                ):
                    match = task
                    break
            if match is None:
                print(
                    f"No ready task compatible with worker '{args.worker_id}'.",
                    file=sys.stderr,
                )
                return 1
            workflow_id, task_id = match.workflow_id, match.task_id

        result = context.dispatcher.dispatch_and_execute(
            workflow_id,
            task_id,
            worker_id=args.worker_id,
        )
        if context.project:
            sync_manifest_state(context.project.root, context.project.state_engine)
        print(format_dispatch_result(result))
        if result.success is False or result.status.value in {
            "error",
            "incompatible",
            "no_worker",
        }:
            return 1
        return 0

    print(format_workers_from_context(context))
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)
    if context.project is None:
        print("No Vedaws project found — run `vedaws init` first.", file=sys.stderr)
        return 1

    if args.state_command == "history":
        print(format_state_history(context.project.state_engine, context.project.name))
        return 0

    if args.state_command == "transition":
        target = ProjectState.parse(args.to_state)
        if target is None:
            print(f"error: unknown state {args.to_state!r}", file=sys.stderr)
            return 1
        trigger = TransitionTrigger.parse(args.trigger) or TransitionTrigger.HUMAN_DECISION
        try:
            context.project.state_engine.transition(target, trigger, args.reason)
            sync_manifest_state(context.project.root, context.project.state_engine)
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(format_current_state(context.project.state_engine, context.project.name))
        return 0

    print(format_current_state(context.project.state_engine, context.project.name))
    return 0


def _load_project_context(args: argparse.Namespace):
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)
    if context.project is None:
        print("No Vedaws project found — run `vedaws init` first.", file=sys.stderr)
        return None
    return context


def cmd_workflow(args: argparse.Namespace) -> int:
    context = _load_project_context(args)
    if context is None:
        return 1
    engine = context.project.workflow_engine
    if engine is None:
        print("Workflow engine not available.", file=sys.stderr)
        return 1

    if args.workflow_command == "show":
        print(format_workflow_detail(engine, args.workflow_id))
        return 0

    if args.workflow_command == "activate":
        try:
            engine.activate(args.workflow_id)
            sync_manifest_state(context.project.root, context.project.state_engine)
        except WorkflowError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(format_workflow_detail(engine, args.workflow_id))
        return 0

    print(format_workflow_list(engine, context.project.name))
    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    context = _load_project_context(args)
    if context is None:
        return 1
    engine = context.project.workflow_engine
    if engine is None:
        print("Workflow engine not available.", file=sys.stderr)
        return 1

    if args.tasks_command in {"complete", "fail"}:
        try:
            workflow_id, task_id = parse_task_ref(args.task_ref)
            if args.tasks_command == "complete":
                engine.complete_task(workflow_id, task_id)
            else:
                engine.fail_task(workflow_id, task_id)
            sync_manifest_state(context.project.root, context.project.state_engine)
        except WorkflowError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(format_task_detail(engine, workflow_id, task_id))
        return 0

    if args.tasks_command == "show":
        try:
            workflow_id, task_id = parse_task_ref(args.task_ref)
        except WorkflowError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(format_task_detail(engine, workflow_id, task_id))
        return 0

    print(format_task_list(engine, context.project.name))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    context = _load_project_context(args)
    if context is None:
        return 1
    if context.dispatcher is None:
        print("Dispatcher not available — workflow engine required.", file=sys.stderr)
        return 1

    summary = run_until_idle(context.dispatcher)
    sync_manifest_state(context.project.root, context.project.state_engine)
    print(format_run_summary(summary))
    if summary.failed > 0 or summary.blocked:
        return 1
    if summary.dispatched == 0 and summary.skipped > 0:
        return 1
    return 0


def _activation_path(workspace: Path, *, use_global: bool) -> Path:
    if not use_global:
        project_path = project_plugins_path(workspace)
        if project_path is not None:
            return project_path
    return global_plugins_path()


def cmd_events(args: argparse.Namespace) -> int:
    workspace = _resolve_workspace_arg(args)
    context = bootstrap(workspace, quiet=not args.verbose)
    if context.event_bus is None:
        print("Event bus not available.", file=sys.stderr)
        return 1
    print(format_event_bus_status(context.event_bus))
    return 0


def cmd_plugins(args: argparse.Namespace) -> int:
    workspace = Path(args.path).resolve()
    context = bootstrap(workspace, quiet=not args.verbose)
    command = getattr(args, "plugins_command", None)

    if command == "info":
        record = context.registry.get(args.plugin_id)
        if record is None:
            print(f"error: plugin '{args.plugin_id}' not found", file=sys.stderr)
            return 1
        print(format_plugin_info(record))
        return 0

    if command == "enable":
        path = _activation_path(workspace, use_global=args.global_config)
        enable_plugin(path, args.plugin_id)
        print(f"Enabled plugin '{args.plugin_id}' in {path}")
        return 0

    if command == "disable":
        path = _activation_path(workspace, use_global=args.global_config)
        disable_plugin(path, args.plugin_id)
        print(f"Disabled plugin '{args.plugin_id}' in {path}")
        return 0

    print(format_plugin_list(context.registry))
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    version_parser = subparsers.add_parser("version", help="Show Vedaws version")
    version_parser.set_defaults(handler=cmd_version)

    init_parser = subparsers.add_parser("init", help="Initialize a Vedaws project")
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace directory, or template id (e.g. software)",
    )
    init_parser.add_argument("--name", help="Project name (default: directory name)")
    init_parser.add_argument(
        "--template",
        metavar="ID",
        help="Project template id (e.g. software)",
    )
    init_parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List project templates from discovered plugins",
    )
    init_parser.set_defaults(handler=cmd_init)

    status_parser = subparsers.add_parser("status", help="Show runtime and project status")
    status_parser.add_argument(
        "-C",
        "--path",
        dest="workspace",
        default=None,
        help="Workspace directory (default: current directory)",
    )
    status_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace directory (legacy positional form)",
    )
    status_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    status_parser.set_defaults(handler=cmd_status)

    doctor_parser = subparsers.add_parser("doctor", help="Run environment health checks")
    doctor_parser.add_argument(
        "-C",
        "--path",
        dest="workspace",
        default=None,
        help="Workspace directory (default: current directory)",
    )
    doctor_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace directory (legacy positional form)",
    )
    doctor_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    doctor_parser.set_defaults(handler=cmd_doctor)

    events_parser = subparsers.add_parser("events", help="Show event bus status and statistics")
    events_parser.add_argument(
        "-C",
        "--path",
        dest="workspace",
        default=None,
        help="Workspace directory (default: current directory)",
    )
    events_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace directory (legacy positional form)",
    )
    events_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    events_parser.set_defaults(handler=cmd_events)

    workers_args = argparse.ArgumentParser(add_help=False)
    workers_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    workers_args.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    workers_parser = subparsers.add_parser(
        "workers",
        parents=[workers_args],
        help="List or run registered workers",
    )
    workers_subparsers = workers_parser.add_subparsers(dest="workers_command")

    workers_run = workers_subparsers.add_parser(
        "run",
        parents=[workers_args],
        help="Run a worker against a ready task",
    )
    workers_run.add_argument("worker_id", help="Worker id")
    workers_run.add_argument(
        "task_ref",
        nargs="?",
        default=None,
        help="Optional task reference (workflow.task); picks next compatible ready task",
    )
    workers_run.set_defaults(workers_command="run")

    workers_parser.set_defaults(handler=cmd_workers, workers_command=None)

    run_parser = subparsers.add_parser(
        "run",
        help="Dispatch and execute all ready tasks until idle",
    )
    run_parser.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    run_parser.set_defaults(handler=cmd_run)

    state_args = argparse.ArgumentParser(add_help=False)
    state_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    state_args.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    state_parser = subparsers.add_parser(
        "state",
        parents=[state_args],
        help="Show or manage project lifecycle state",
    )
    state_subparsers = state_parser.add_subparsers(dest="state_command")

    state_history = state_subparsers.add_parser(
        "history",
        parents=[state_args],
        help="Show project state history",
    )
    state_history.set_defaults(state_command="history")

    state_transition = state_subparsers.add_parser(
        "transition",
        parents=[state_args],
        help="Transition project to a new state",
    )
    state_transition.add_argument("to_state", help="Target state")
    state_transition.add_argument("--reason", help="Optional reason for the transition")
    state_transition.add_argument(
        "--trigger",
        default=TransitionTrigger.HUMAN_DECISION.value,
        help="Transition trigger category",
    )
    state_transition.set_defaults(state_command="transition")

    state_parser.set_defaults(handler=cmd_state, state_command=None)

    workflow_args = argparse.ArgumentParser(add_help=False)
    workflow_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    workflow_args.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    workflow_parser = subparsers.add_parser(
        "workflow",
        parents=[workflow_args],
        help="List and manage project workflows",
    )
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command")

    workflow_show = workflow_subparsers.add_parser(
        "show",
        parents=[workflow_args],
        help="Show workflow definition and progress",
    )
    workflow_show.add_argument("workflow_id", help="Workflow id")
    workflow_show.set_defaults(workflow_command="show")

    workflow_activate = workflow_subparsers.add_parser(
        "activate",
        parents=[workflow_args],
        help="Activate a workflow and initialize its tasks",
    )
    workflow_activate.add_argument("workflow_id", help="Workflow id")
    workflow_activate.set_defaults(workflow_command="activate")

    workflow_parser.set_defaults(handler=cmd_workflow, workflow_command=None)

    tasks_args = argparse.ArgumentParser(add_help=False)
    tasks_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    tasks_args.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    tasks_parser = subparsers.add_parser(
        "tasks",
        parents=[tasks_args],
        help="List and manage project tasks",
    )
    tasks_subparsers = tasks_parser.add_subparsers(dest="tasks_command")

    tasks_show = tasks_subparsers.add_parser(
        "show",
        parents=[tasks_args],
        help="Show task details",
    )
    tasks_show.add_argument("task_ref", help="Task reference (workflow.task)")
    tasks_show.set_defaults(tasks_command="show")

    tasks_complete = tasks_subparsers.add_parser(
        "complete",
        parents=[tasks_args],
        help="Record a successful task outcome (no worker execution)",
    )
    tasks_complete.add_argument("task_ref", help="Task reference (workflow.task)")
    tasks_complete.set_defaults(tasks_command="complete")

    tasks_fail = tasks_subparsers.add_parser(
        "fail",
        parents=[tasks_args],
        help="Record a failed task outcome (no worker execution)",
    )
    tasks_fail.add_argument("task_ref", help="Task reference (workflow.task)")
    tasks_fail.set_defaults(tasks_command="fail")

    tasks_parser.set_defaults(handler=cmd_tasks, tasks_command=None)

    plugins_args = argparse.ArgumentParser(add_help=False)
    plugins_args.add_argument(
        "-C",
        "--path",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    plugins_args.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    plugins_parser = subparsers.add_parser(
        "plugins",
        parents=[plugins_args],
        help="List and manage Vedaws plugins",
    )
    plugins_subparsers = plugins_parser.add_subparsers(dest="plugins_command")

    plugins_list = plugins_subparsers.add_parser(
        "list",
        parents=[plugins_args],
        help="List discovered plugins and lifecycle status",
    )
    plugins_list.set_defaults(plugins_command="list")

    plugins_info = plugins_subparsers.add_parser(
        "info",
        parents=[plugins_args],
        help="Show plugin manifest and contribution details",
    )
    plugins_info.add_argument("plugin_id", help="Plugin id")
    plugins_info.set_defaults(plugins_command="info")

    plugins_enable = plugins_subparsers.add_parser(
        "enable",
        parents=[plugins_args],
        help="Enable a plugin in project or global activation config",
    )
    plugins_enable.add_argument("plugin_id", help="Plugin id")
    plugins_enable.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Update global ~/.vedaws/plugins.toml instead of project config",
    )
    plugins_enable.set_defaults(plugins_command="enable")

    plugins_disable = plugins_subparsers.add_parser(
        "disable",
        parents=[plugins_args],
        help="Disable a plugin in project or global activation config",
    )
    plugins_disable.add_argument("plugin_id", help="Plugin id")
    plugins_disable.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Update global ~/.vedaws/plugins.toml instead of project config",
    )
    plugins_disable.set_defaults(plugins_command="disable")

    plugins_parser.set_defaults(handler=cmd_plugins, plugins_command=None)
