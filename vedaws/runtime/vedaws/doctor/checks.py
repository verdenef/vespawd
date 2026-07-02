"""Health checks for vedaws doctor."""

from __future__ import annotations

import os
from pathlib import Path

from vedaws.ai.validator import validate_ai_platform
from vedaws.automation.loader import load_all_rules
from vedaws.automation.validator import validate_rules
from vedaws.config.loader import load_config
from vedaws.config.paths import user_config_dir
from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.runtime.bootstrap import bootstrap
from vedaws.runtime.context import RuntimeContext


def run_health_checks(
    workspace: Path | None = None, *, quiet: bool = False
) -> list[HealthCheckResult]:
    workspace = (workspace or Path.cwd()).resolve()
    return [
        check_configuration(workspace),
        check_runtime(workspace, quiet=quiet),
        check_plugin_registry(workspace, quiet=quiet),
        check_plugin_platform(workspace, quiet=quiet),
        check_plugin_health_checks(workspace, quiet=quiet),
        check_plugin_security(workspace, quiet=quiet),
        check_event_bus(workspace, quiet=quiet),
        check_automation(workspace, quiet=quiet),
        check_ai_platform(workspace, quiet=quiet),
        check_worker_registry(workspace, quiet=quiet),
        check_worker_discovery(workspace, quiet=quiet),
        check_invalid_workers(workspace, quiet=quiet),
        check_duplicate_workers(workspace, quiet=quiet),
        check_project_state(workspace, quiet=quiet),
        check_workflows(workspace, quiet=quiet),
        check_dispatcher(workspace, quiet=quiet),
        check_execution_pipeline(workspace, quiet=quiet),
        check_workspace(workspace, quiet=quiet),
        check_permissions(workspace),
    ]


def check_configuration(workspace: Path) -> HealthCheckResult:
    try:
        config = load_config(workspace)
        message = (
            f"Configuration loaded — log level {config.logging.level}, "
            f"plugins {'enabled' if config.plugins.enabled else 'disabled'}"
        )
        return HealthCheckResult("configuration", CheckStatus.PASS, message)
    except Exception as exc:  # noqa: BLE001 — health check boundary
        return HealthCheckResult("configuration", CheckStatus.FAIL, str(exc))


def check_runtime(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        if context.status.value != "active":
            return HealthCheckResult(
                "runtime",
                CheckStatus.FAIL,
                f"Runtime status is {context.status}, expected active",
            )
        return HealthCheckResult(
            "runtime",
            CheckStatus.PASS,
            f"Runtime bootstrap succeeded — status {context.status}",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("runtime", CheckStatus.FAIL, str(exc))


def check_plugin_registry(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        count = context.plugin_count
        active = context.active_plugin_count
        if count == 0:
            return HealthCheckResult(
                "plugin registry",
                CheckStatus.WARN,
                "No plugins discovered — registry is empty",
            )
        names = ", ".join(plugin.id for plugin in context.registry.list_plugins())
        return HealthCheckResult(
            "plugin registry",
            CheckStatus.PASS,
            f"{count} plugin(s) discovered ({active} active): {names}",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("plugin registry", CheckStatus.FAIL, str(exc))


def check_plugin_platform(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        registry = context.registry
        issues: list[str] = []

        if registry.invalid_count:
            issues.append(f"{registry.invalid_count} invalid manifest(s)")
        if registry.duplicate_count:
            issues.append(f"{registry.duplicate_count} duplicate id(s)")
        failed = [
            record.id for record in registry.list_records() if record.status.value == "failed"
        ]
        if failed:
            issues.append(f"failed activation: {', '.join(failed)}")
        if context.plugin_activation_errors:
            issues.extend(context.plugin_activation_errors)

        if issues:
            return HealthCheckResult(
                "plugin platform",
                CheckStatus.FAIL,
                "; ".join(issues),
            )
        return HealthCheckResult(
            "plugin platform",
            CheckStatus.PASS,
            f"Plugin lifecycle healthy — {registry.active_count} active plugin(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("plugin platform", CheckStatus.FAIL, str(exc))


def check_plugin_health_checks(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        checks = context.registry.aggregated_contributions.health_checks
        if not checks:
            return HealthCheckResult(
                "plugin health checks",
                CheckStatus.WARN,
                "No plugin health checks registered",
            )
        failures: list[str] = []
        warnings: list[str] = []
        previous = Path.cwd()
        try:
            import os

            os.chdir(workspace)
            for check in checks:
                result = check()
                if result.failed:
                    failures.append(f"{result.name}: {result.message}")
                elif result.warning:
                    warnings.append(f"{result.name}: {result.message}")
        finally:
            import os

            os.chdir(previous)
        if failures:
            return HealthCheckResult(
                "plugin health checks",
                CheckStatus.FAIL,
                "; ".join(failures),
            )
        if warnings:
            return HealthCheckResult(
                "plugin health checks",
                CheckStatus.WARN,
                "; ".join(warnings),
            )
        return HealthCheckResult(
            "plugin health checks",
            CheckStatus.PASS,
            f"{len(checks)} plugin health check(s) passed",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("plugin health checks", CheckStatus.FAIL, str(exc))


def check_plugin_security(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        active = context.registry.list_active()
        if not active:
            return HealthCheckResult(
                "plugin security",
                CheckStatus.WARN,
                "No active plugins to evaluate security declarations",
            )

        warnings: list[str] = []
        for record in active:
            security = record.manifest.security
            if (
                "subprocess.exec" in security.permissions
                and not security.subprocess_allow
            ):
                warnings.append(
                    f"{record.id}: subprocess.exec declared without subprocess_allow list"
                )
            if (
                security.network == "none"
                and "network.outbound" in security.permissions
            ):
                warnings.append(
                    f"{record.id}: network.outbound permission declared while network=none"
                )

        if warnings:
            return HealthCheckResult(
                "plugin security",
                CheckStatus.WARN,
                "; ".join(warnings),
            )

        declared = sum(1 for record in active if record.manifest.security.permissions)
        return HealthCheckResult(
            "plugin security",
            CheckStatus.PASS,
            f"{declared}/{len(active)} active plugin(s) declare explicit permissions",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("plugin security", CheckStatus.FAIL, str(exc))


def check_event_bus(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        bus = context.event_bus
        if bus is None:
            return HealthCheckResult(
                "event bus",
                CheckStatus.FAIL,
                "Event bus was not initialized during bootstrap",
            )
        stats = bus.stats()
        if stats.subscriber_count < 0:
            return HealthCheckResult(
                "event bus",
                CheckStatus.FAIL,
                "Subscriber registry is invalid",
            )
        return HealthCheckResult(
            "event bus",
            CheckStatus.PASS,
            f"Event bus initialized — {stats.subscriber_count} subscriber(s), "
            f"{stats.total_published} event(s) published, "
            f"{len(stats.known_event_types)} registered type(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("event bus", CheckStatus.FAIL, str(exc))


def check_automation(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        engine = context.automation_engine
        if engine is None:
            return HealthCheckResult(
                "automation",
                CheckStatus.FAIL,
                "Automation engine was not initialized",
            )
        rules = load_all_rules(
            workspace,
            plugin_contributions=context.registry.aggregated_contributions,
        )
        report = validate_rules(
            rules,
            worker_registry=context.worker_registry,
            plugin_registry=context.registry,
        )
        enabled = sum(1 for rule in rules if rule.enabled)
        event_bindings = len({rule.on_event for rule in rules})
        if report.error_count:
            return HealthCheckResult(
                "automation",
                CheckStatus.FAIL,
                f"{report.error_count} rule error(s), {enabled}/{len(rules)} enabled, "
                f"{event_bindings} event binding(s)",
            )
        if report.warning_count:
            return HealthCheckResult(
                "automation",
                CheckStatus.WARN,
                f"{report.warning_count} rule warning(s), {enabled}/{len(rules)} enabled, "
                f"{event_bindings} event binding(s)",
            )
        if not rules:
            return HealthCheckResult(
                "automation",
                CheckStatus.WARN,
                "Automation engine ready — no rules registered",
            )
        return HealthCheckResult(
            "automation",
            CheckStatus.PASS,
            f"{len(rules)} rule(s), {enabled} enabled, {event_bindings} event binding(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("automation", CheckStatus.FAIL, str(exc))


def check_ai_platform(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        service = context.ai_service
        if service is None:
            return HealthCheckResult(
                "ai platform",
                CheckStatus.FAIL,
                "AI service was not initialized",
            )
        validation = validate_ai_platform(service.registry, service.router.config)
        provider_count = service.registry.count
        capability_count = len(service.list_capabilities())
        if validation.error_count:
            return HealthCheckResult(
                "ai platform",
                CheckStatus.FAIL,
                f"{validation.error_count} error(s), {provider_count} provider(s), "
                f"{capability_count} capability binding(s)",
            )
        if validation.warning_count:
            return HealthCheckResult(
                "ai platform",
                CheckStatus.WARN,
                f"{validation.warning_count} warning(s), {provider_count} provider(s), "
                f"{capability_count} capability binding(s)",
            )
        if provider_count == 0:
            return HealthCheckResult(
                "ai platform",
                CheckStatus.WARN,
                "AI platform ready — no providers registered",
            )
        return HealthCheckResult(
            "ai platform",
            CheckStatus.PASS,
            f"{provider_count} provider(s), {capability_count} capability binding(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("ai platform", CheckStatus.FAIL, str(exc))


def check_worker_registry(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        registry = context.worker_registry
        if registry.count == 0:
            return HealthCheckResult(
                "worker registry",
                CheckStatus.WARN,
                "Worker registry initialized but empty",
            )
        return HealthCheckResult(
            "worker registry",
            CheckStatus.PASS,
            f"Worker registry initialized with {registry.count} worker(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("worker registry", CheckStatus.FAIL, str(exc))


def check_worker_discovery(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        discovery = context.worker_registry.discovery
        if discovery is None:
            return HealthCheckResult(
                "worker discovery",
                CheckStatus.FAIL,
                "Worker discovery did not run",
            )
        return HealthCheckResult(
            "worker discovery",
            CheckStatus.PASS,
            f"Worker discovery completed — {discovery.worker_count} worker(s) found",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("worker discovery", CheckStatus.FAIL, str(exc))


def check_invalid_workers(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        invalid = context.worker_registry.invalid_count
        if invalid == 0:
            return HealthCheckResult(
                "invalid workers",
                CheckStatus.PASS,
                "No invalid worker manifests detected",
            )
        return HealthCheckResult(
            "invalid workers",
            CheckStatus.WARN,
            f"{invalid} invalid worker manifest(s) detected",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("invalid workers", CheckStatus.FAIL, str(exc))


def check_duplicate_workers(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        duplicates = context.worker_registry.duplicate_count
        if duplicates == 0:
            return HealthCheckResult(
                "duplicate worker ids",
                CheckStatus.PASS,
                "No duplicate worker IDs detected",
            )
        return HealthCheckResult(
            "duplicate worker ids",
            CheckStatus.WARN,
            f"{duplicates} duplicate worker ID(s) detected — extras skipped",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("duplicate worker ids", CheckStatus.FAIL, str(exc))


def check_project_state(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        if context.project is None:
            return HealthCheckResult(
                "project state",
                CheckStatus.WARN,
                "No project — state machine not applicable",
            )
        engine = context.project.state_engine
        engine.validate()
        return HealthCheckResult(
            "project state",
            CheckStatus.PASS,
            f"Project state valid — current state is {engine.current.value}",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("project state", CheckStatus.FAIL, str(exc))


def check_workflows(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        if context.project is None:
            return HealthCheckResult(
                "workflows",
                CheckStatus.WARN,
                "No project — workflow engine not applicable",
            )
        engine = context.project.workflow_engine
        if engine is None:
            return HealthCheckResult(
                "workflows",
                CheckStatus.FAIL,
                "Workflow engine did not load",
            )
        invalid = len(engine.load_result.invalid)
        workflows = len(engine.list_workflows())
        if workflows == 0:
            return HealthCheckResult(
                "workflows",
                CheckStatus.WARN,
                "No workflow definitions found in .vedaws/workflows/",
            )
        if invalid:
            return HealthCheckResult(
                "workflows",
                CheckStatus.WARN,
                f"{workflows} workflow(s) loaded, {invalid} invalid manifest(s)",
            )
        return HealthCheckResult(
            "workflows",
            CheckStatus.PASS,
            f"{workflows} workflow definition(s) loaded",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("workflows", CheckStatus.FAIL, str(exc))


def check_dispatcher(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        if context.project is None:
            return HealthCheckResult(
                "dispatcher",
                CheckStatus.WARN,
                "No project — dispatcher not applicable",
            )
        if context.dispatcher is None:
            return HealthCheckResult(
                "dispatcher",
                CheckStatus.FAIL,
                "Worker dispatcher did not initialize",
            )
        executable = len(context.worker_registry.list_executable())
        return HealthCheckResult(
            "dispatcher",
            CheckStatus.PASS,
            f"Dispatcher ready — {executable} executable worker(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("dispatcher", CheckStatus.FAIL, str(exc))


def check_execution_pipeline(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    try:
        context = bootstrap(workspace, quiet=quiet)
        if context.project is None or context.dispatcher is None:
            return HealthCheckResult(
                "execution pipeline",
                CheckStatus.WARN,
                "No project — execution pipeline not applicable",
            )

        engine = context.project.workflow_engine
        if engine is None:
            return HealthCheckResult(
                "execution pipeline",
                CheckStatus.FAIL,
                "Workflow engine not loaded",
            )

        uncovered: list[str] = []
        for workflow in engine.list_workflows():
            for task_def in workflow.tasks:
                if not task_def.capability:
                    continue
                if not context.dispatcher.find_worker_for_task(task_def):
                    uncovered.append(f"{workflow.id}.{task_def.id}:{task_def.capability}")

        if uncovered:
            return HealthCheckResult(
                "execution pipeline",
                CheckStatus.WARN,
                f"No executable worker for {len(uncovered)} task capability(s): "
                + ", ".join(uncovered[:5]),
            )
        return HealthCheckResult(
            "execution pipeline",
            CheckStatus.PASS,
            "All workflow task capabilities have compatible executable workers",
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheckResult("execution pipeline", CheckStatus.FAIL, str(exc))


def check_workspace(workspace: Path, *, quiet: bool = False) -> HealthCheckResult:
    if not workspace.exists():
        return HealthCheckResult("workspace", CheckStatus.FAIL, f"Path does not exist: {workspace}")
    if not workspace.is_dir():
        return HealthCheckResult("workspace", CheckStatus.FAIL, f"Not a directory: {workspace}")

    project = bootstrap(workspace, quiet=quiet).project
    if project is None:
        return HealthCheckResult(
            "workspace",
            CheckStatus.WARN,
            f"No Vedaws project in {workspace} — run `vedaws init` to initialize",
        )
    return HealthCheckResult(
        "workspace",
        CheckStatus.PASS,
        f"Project '{project.name}' detected at {project.root}",
    )


def check_permissions(workspace: Path) -> HealthCheckResult:
    issues: list[str] = []

    user_dir = user_config_dir()
    if not _is_writable(user_dir, create=True):
        issues.append(f"Cannot write user config directory: {user_dir}")

    vedaws_dir = workspace / ".vedaws"
    if vedaws_dir.exists() and not _is_writable(vedaws_dir):
        issues.append(f"Cannot write project config directory: {vedaws_dir}")

    if issues:
        return HealthCheckResult("permissions", CheckStatus.FAIL, "; ".join(issues))

    if not os.access(workspace, os.W_OK):
        return HealthCheckResult(
            "permissions",
            CheckStatus.WARN,
            f"Workspace is not writable: {workspace}",
        )

    return HealthCheckResult("permissions", CheckStatus.PASS, "Required paths are writable")


def _is_writable(path: Path, create: bool = False) -> bool:
    try:
        if create:
            path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".vedaws_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True
    except OSError:
        return False


def overall_status(results: list[HealthCheckResult]) -> CheckStatus:
    if any(result.failed for result in results):
        return CheckStatus.FAIL
    if any(result.warning for result in results):
        return CheckStatus.WARN
    return CheckStatus.PASS
