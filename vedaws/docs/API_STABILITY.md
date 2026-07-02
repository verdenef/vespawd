# Vedaws API Stability — v0.5

**Architecture version:** 0.5.0  
**Implementation baseline:** Milestones 6–16  
**Companion:** [`ARCHITECTURE_FREEZE_V0.5.md`](ARCHITECTURE_FREEZE_V0.5.md)  
**Source audit:** [`ARCHITECTURE_REVIEW_V0.5.md`](ARCHITECTURE_REVIEW_V0.5.md)

---

## Purpose

This document lists **public contracts frozen at architecture v0.5**. It is the contributor reference for what must remain stable across releases until an explicit architecture review and version bump.

**Rules:**

1. Symbols and formats in §Frozen APIs must not change incompatibly without a documented architecture review.
2. §Unstable and deferred APIs may change or be removed — do not build production integrations on them.
3. §Internal APIs are not supported for external use.
4. This document describes **what exists today**; it does not add new APIs.

**Semver guidance (v0.5):**

| Change type | Policy |
|-------------|--------|
| Breaking change to §Frozen APIs | Requires architecture review + minor/major version policy decision before v1 |
| Additive frozen API (new action type, new event, new optional TOML key) | Allowed if design doc updated same milestone |
| Internal refactor with no contract change | Allowed |
| Deferred API completion | May ship as additive without breaking frozen subset |

---

## Frozen APIs by subsystem

### Runtime

| Symbol | Package / module | Notes |
|--------|------------------|-------|
| `bootstrap(workspace, *, quiet=False) -> RuntimeContext` | `vedaws.runtime.bootstrap` | Single composition root |
| `shutdown(context) -> None` | `vedaws.runtime.bootstrap` | Reverses plugin and automation subscriptions |
| `RuntimeContext` | `vedaws.runtime.context` | Session façade |
| `RuntimeStatus` | `vedaws.runtime.status` | `ACTIVE`, `STOPPING`, `INACTIVE` |

**Frozen `RuntimeContext` fields:**

| Field | Type (conceptual) |
|-------|-------------------|
| `config` | `VedawsConfig` |
| `registry` | `PluginRegistry` |
| `worker_registry` | `WorkerRegistry` |
| `project` | `ProjectContext \| None` |
| `dispatcher` | `WorkerDispatcher \| None` |
| `event_bus` | `EventBus \| None` |
| `ai_service` | `AIService \| None` |
| `automation_engine` | `AutomationEngine \| None` |

Additional fields (`workspace`, `status`, `version`, `plugin_platform`, `plugin_activation_errors`) exist on the dataclass; CLI and doctor rely on them. Treat the full `RuntimeContext` dataclass shape as stable for v0.5.

**Design reference:** [`design/003_RUNTIME.md`](../design/003_RUNTIME.md)

---

### CLI

| Symbol | Notes |
|--------|-------|
| Entry point `vedaws.cli.app:main` | `pyproject.toml` `[project.scripts]` |

**Frozen top-level commands:**

| Command | Purpose |
|---------|---------|
| `version` | Show package version |
| `init` | Initialize project (`--template`, `--name`, workspace) |
| `status` | Runtime and project status |
| `doctor` | Environment health checks |
| `events` | Event bus statistics |
| `workers` | Worker listing and `workers run` |
| `run` | Dispatch ready workflow tasks |
| `state` | `history`, `transition` subcommands |
| `workflow` | `show`, `activate` subcommands |
| `tasks` | `show`, `complete`, `fail` subcommands |
| `plugins` | `list`, `info`, `enable`, `disable` |
| `automation` | `list`, `enable`, `disable`, `run` |
| `ai` | `providers`, `capabilities`, `status` |

Plugin commands are registered dynamically (e.g. `vedaws git`, `vedaws software`, `vedaws unity`). Command **names** contributed via the plugin SDK are stable per plugin release, not per Vedaws core semver.

**Design reference:** [`design/003_RUNTIME.md`](../design/003_RUNTIME.md)

---

### Configuration

| Symbol | Package | Notes |
|--------|---------|-------|
| `load_config(workspace) -> VedawsConfig` | `vedaws.config.loader` | Merge order: defaults → user → project → env |
| `VedawsConfig.merge()` | `vedaws.config.schema` | Layer merging |
| `VedawsConfig` sections | `vedaws.config.schema` | `[logging]`, `[plugins]`, `[workers]`, `[runtime]`, `[ai]`, `[security]` |

**Frozen `[ai]` TOML shape:**

```toml
[ai]
default_provider = "<provider-id>"

[ai.capabilities.<capability-name>]
preferred = "<provider-id>"
fallback = ["<provider-id>", ...]
```

Environment variables documented in [`design/012_CONFIGURATION.md`](../design/012_CONFIGURATION.md) for `[logging]`, `[plugins]`, `[workers]`, `[runtime]` are part of the contract.

**Frozen `[security]` TOML shape (M14 additive):**

```toml
[security]
allow_env_secrets = true
allow_file_secrets = false
```

**Design reference:** [`design/012_CONFIGURATION.md`](../design/012_CONFIGURATION.md)

---

### Project model

| Symbol | Package | Notes |
|--------|---------|-------|
| `init_project(workspace, name, *, template=...)` | `vedaws.project.init` | Scaffolds `.vedaws/` |
| `discover_project_templates(config)` | `vedaws.project.templates` | Plugin-contributed templates |
| `apply_project_template(...)` | `vedaws.project.templates` | Template install |

**Frozen `.vedaws/` layout contract:**

```
.vedaws/
├── project.toml
├── config.toml
├── plugins.toml
├── state.toml              # Authoritative project state
├── transitions.jsonl
├── workflow-progress.json
├── automation.toml
└── workflows/
    └── *.workflow.toml
```

- Project root = directory containing `.vedaws/project.toml`.
- `state.toml` is authoritative; `project.toml` `[project].state` is a mirror only.

**Design reference:** [`design/007_PROJECT_MODEL.md`](../design/007_PROJECT_MODEL.md)

---

### State machine

| Symbol | Package | Notes |
|--------|---------|-------|
| `ProjectState` | `vedaws.project.state.states` | Enum values below |
| `StateEngine.transition()` | `vedaws.project.state.engine` | Authorized transitions |
| `StateEngine.current` | `vedaws.project.state.engine` | Current state |
| `allows_dispatch(state)` | `vedaws.project.state.eligibility` | Dispatch gate |
| `allows_orchestration(state)` | `vedaws.project.state.eligibility` | Workflow/task recording gate |

**Frozen `ProjectState` values:**

`created`, `initialized`, `planning`, `ready`, `executing`, `awaiting_approval`, `completed`, `blocked`, `failed`, `recovering`, `archived`

**Design reference:** [`design/006_STATE_MACHINE.md`](../design/006_STATE_MACHINE.md)

---

### Workflow engine

| Symbol | Package | Notes |
|--------|---------|-------|
| `WorkflowEngine.activate()` | `vedaws.workflow.engine` | Activate workflow by id |
| `WorkflowEngine.get_workflow()` | `vedaws.workflow.engine` | Lookup loaded workflow |
| Task outcome recording | `vedaws.workflow.engine` | `complete_task`, `fail_task` paths |
| `parse_task_ref(ref) -> (workflow_id, task_id)` | `vedaws.workflow.engine` | Format: `workflow.task` |

**Frozen workflow TOML schema (per file):**

| Element | Contract |
|---------|----------|
| Workflow id | File stem or explicit `id` in manifest |
| `[[tasks]]` | Task definitions |
| `depends_on` | Task dependency list |
| `capability` | String matched against worker capabilities |
| `ai_capability` | Optional AI capability alias used by AI workers |
| `skills` / `skill` | Optional skill metadata references used by worker execution guidance |

File suffix: `*.workflow.toml` (see `WORKFLOW_MANIFEST_SUFFIX` in `vedaws.workflow.manifest`).

**Design reference:** [`design/003_RUNTIME.md`](../design/003_RUNTIME.md), [`design/006_STATE_MACHINE.md`](../design/006_STATE_MACHINE.md)

---

### Worker system

| Symbol | Package | Notes |
|--------|---------|-------|
| `Worker` | `vedaws.workers.interface` | Base worker ABC |
| `ExecutableWorker` | `vedaws.workers.interface` | Workers that execute tasks |
| `AIExecutableWorker` | `vedaws.workers.ai_worker` | AI worker base bound to `AIService` |
| `WorkerMetadata`, `WorkerCapability` | `vedaws.workers.models` | Discovery metadata |
| `TaskDispatch` | `vedaws.workers.execution` | Input to `execute()` |
| `TaskOutcome`, `TaskOutcomeStatus` | `vedaws.workers.execution` | Worker result |
| `WorkerRegistry.register()`, `get()`, `list_executable()`, `wire_ai_service()`, `wire_skills()` | `vedaws.workers.registry` | Registry operations |

**Frozen execution contract:**

- Workers are selected by **capability string match**, not worker implementation type.
- `TaskDispatch` fields: `workflow_id`, `task_id`, `task`, `project_name`, `instructions`.
- `TaskOutcomeStatus`: `success`, `failure`, `partial`, `escalation`.

**Design reference:** [`design/004_WORKERS.md`](../design/004_WORKERS.md)

---

### Dispatcher

| Symbol | Package | Notes |
|--------|---------|-------|
| `DispatchResult`, `DispatchStatus` | `vedaws.dispatch.models` | Per-dispatch result |
| `WorkerDispatcher.dispatch_and_execute(workflow_id, task_id, *, worker_id=None)` | `vedaws.dispatch.dispatcher` | Synchronous dispatch |
| `WorkerDispatcher.list_ready_tasks()` | `vedaws.dispatch.dispatcher` | Ready task enumeration |
| `WorkerDispatcher.find_worker_for_task()` | `vedaws.dispatch.dispatcher` | Capability matching |

**Frozen `DispatchStatus` values:** `dispatched`, `no_worker`, `no_task`, `incompatible`, `error`, `skipped`

**Design reference:** [`design/004_WORKERS.md`](../design/004_WORKERS.md)

---

### Event bus

| Symbol | Package | Notes |
|--------|---------|-------|
| `Event`, `create_event()` | `vedaws.events.model` | Immutable event records |
| `EventBus.publish()`, `subscribe()`, `unsubscribe()` | `vedaws.events.bus` | Synchronous dispatch |
| `EventType` | `vedaws.events.types` | System event constants |

**Frozen system event types:**

`ProjectInitialized`, `ProjectStateChanged`, `WorkflowStarted`, `WorkflowCompleted`, `TaskCreated`, `TaskStarted`, `TaskCompleted`, `TaskFailed`, `WorkerRegistered`, `WorkerStarted`, `WorkerCompleted`, `PluginLoaded`, `PluginUnloaded`

Custom event type strings are allowed for application use; automation rules may reference them.

**Design reference:** [`design/003_RUNTIME.md`](../design/003_RUNTIME.md)

---

### Plugin platform

| Symbol | Package | Notes |
|--------|---------|-------|
| `VedawsPlugin` | `vedaws.plugins.sdk` | Plugin base class |
| `PluginContext` | `vedaws.plugins.sdk` | Contribution context |
| `PluginManifest`, `PluginDependency` | `vedaws.plugins.manifest` | Manifest v1 model |
| `PluginPlatform.run()` | `vedaws.plugins.platform` | Discovery → activation |
| `PluginRegistry.list_active()` | `vedaws.plugins.registry` | Active plugins |
| `discover_plugins` | `vedaws.plugins.discovery` | Filesystem discovery |
| `resolve_dependencies` | `vedaws.plugins.dependencies` | Dependency ordering |

**Frozen `PluginContext.contribute_*` methods (SDK surface):**

| Method | Contribution |
|--------|--------------|
| `contribute_worker(worker)` | Executable or manifest worker |
| `contribute_command(name, ...)` | CLI command |
| `contribute_workflow_template(path)` | Workflow template file |
| `contribute_project_template(template_id, ...)` | Project template |
| `contribute_skill(skill_id, name, ...)` | Skill metadata — runtime-consumable by worker execution (first consumer in M16) |
| `contribute_health_check(check)` | Doctor health check |
| `contribute_configuration(schema)` | Config schema — merged/validated during bootstrap (M16 additive) |
| `contribute_automation_rule(rule)` | Automation rule |
| `contribute_ai_provider(provider)` | AI provider |
| `subscribe_event(event_type, handler, ...)` | Event subscription |

**Frozen `vedaws.plugin.toml` manifest v1:** `manifest_version = "1"`, required fields `id`, `name`, `version`, `entry_point`; optional `dependencies`, `compatibility`, `capabilities`, `security`.

**Frozen optional `[security]` plugin manifest shape (M14 additive):**

```toml
[security]
permissions = ["filesystem.read", "filesystem.write", "subprocess.exec", "network.outbound"]
subprocess_allow = ["git"]
network = "none" # or "outbound"
```

**Frozen `plugins.toml` activation format:**

```toml
[plugins]
enabled = ["plugin-id", ...]   # optional allow-list
disabled = ["plugin-id", ...]  # deny-list
```

**Design reference:** [`design/010_PLUGINS.md`](../design/010_PLUGINS.md)

---

### Automation engine

| Symbol | Package | Notes |
|--------|---------|-------|
| `AutomationRule` | `vedaws.automation.model` | Rule definition |
| `RuleCondition`, `RuleAction` | `vedaws.automation.model` | Condition and action models |
| `contribute_automation_rule(rule)` | `vedaws.plugins.sdk` | Plugin registration |
| Action type constants | `vedaws.automation.model` | See below |

**Frozen rule shape:**

| Field | Alias | Description |
|-------|-------|-------------|
| `id` | — | Unique rule id |
| `on_event` | — | Event type string |
| `conditions` / `if` | — | Payload matchers (all must match) |
| `actions` / `then` | — | Ordered action list |
| `enabled` | — | Per-rule flag |

**Frozen action types:**

| Type | Purpose |
|------|---------|
| `execute_worker` | Run worker (`worker_id`, optional `task_ref`) |
| `publish_event` | Publish event (depth-limited) |
| `transition_state` | Project state transition |
| `workflow_step` | Dispatch / complete / fail task |
| `plugin_command` | Invoke plugin CLI handler |

**Frozen `.vedaws/automation.toml`:** `[automation]` section, `[[rules]]` entries, `[automation.overrides."<rule-id>"]` for per-rule enable/disable.

**CLI:** `vedaws automation list|enable|disable|run`

**Design reference:** [`design/005_AUTOMATION.md`](../design/005_AUTOMATION.md)

---

### AI provider SDK

| Symbol | Package | Notes |
|--------|---------|-------|
| `AIProvider` | `vedaws.ai.provider` | Provider plugin ABC |
| `AIService` | `vedaws.ai.service` | Runtime façade on `RuntimeContext` |
| `contribute_ai_provider(provider)` | `vedaws.plugins.sdk` | Plugin registration |
| `STANDARD_AI_CAPABILITIES` | `vedaws.ai.capabilities` | Capability constants |

**Frozen `AIProvider` interface methods:**

| Method | Required |
|--------|----------|
| `id`, `name`, `capabilities` | Yes (properties) |
| `health()` | Yes |
| `chat(request)` | Yes |
| `generate(request)` | Yes |
| `stream(request)` | Optional (default raises `NotImplementedError`) |
| `embeddings(request)` | Optional (default raises `NotImplementedError`) |

**Frozen `AIService` methods:**

`list_providers()`, `list_capabilities()`, `resolve_provider(capability)`, `resolve_chain(capability)`, `provider_health(provider_id=None)`, `chat(request)`, `generate(request)`, `stream(request)`, `embeddings(request)`

**Frozen standard AI capabilities:**

`chat`, `plan`, `implement`, `review`, `summarize`, `document`, `refactor`, `explain`

Routing uses `[ai]` / `[ai.capabilities.*]` config (see Configuration section).

**Design reference:** [`design/017_AI_PROVIDERS.md`](../design/017_AI_PROVIDERS.md)

---

### Automation and AI model types (plugin authors)

| Symbol | Package |
|--------|---------|
| `AutomationRule`, `RuleCondition`, `RuleAction` | `vedaws.automation.model` |
| `ChatRequest`, `ChatResponse`, `GenerateRequest`, `GenerateResponse` | `vedaws.ai.model` |
| `Event`, `EventType`, `create_event` | `vedaws.events` |

---

## Stable file formats

| Format | Location | Version |
|--------|----------|---------|
| Project manifest | `.vedaws/project.toml` | Implicit v0.5 |
| Project state | `.vedaws/state.toml` | Implicit v0.5 |
| State history | `.vedaws/transitions.jsonl` | Append-only JSON lines |
| Workflow progress | `.vedaws/workflow-progress.json` | Implicit v0.5 |
| Automation rules | `.vedaws/automation.toml` | M11 schema |
| Workflow definitions | `.vedaws/workflows/*.workflow.toml` | M4+ schema |
| Plugin manifest | `vedaws.plugin.toml` | **v1** (`manifest_version = "1"`) |
| Plugin activation | `plugins.toml` / `.vedaws/plugins.toml` | v0.5 |
| Vedaws config | `config.toml` / `.vedaws/config.toml` | Sections in `012_CONFIGURATION.md` |

No formal `.vedaws/` schema version field exists at v0.5 freeze (deferred per review).

---

## Unstable and deferred APIs

Do **not** treat these as stable integrations.

| API / surface | Status | Guidance |
|---------------|--------|----------|
| `contribute_skill()` | Implemented consumer path | Skills are runtime-consumable metadata (first consumer: `AIExecutableWorker`) |
| `contribute_configuration()` | Implemented merge path | Schemas are merged/validated into `VedawsConfig.extensions` during bootstrap |
| `VedawsConfig.extensions` | Escape hatch | Untyped; may change |
| Event `payload` dicts | Informal | No enforced schema at v0.5 |
| `AIService` from worker `execute()` | Implemented in M13 | Use `AIExecutableWorker` + capability routing |
| `invoke_ai` automation action | Not implemented | Use `execute_worker` or manual integration |
| `AIProvider.stream()` / `embeddings()` | Stub platform-wide | Optional per provider |
| Plugin event publish from SDK | Subscribe only | No `publish` on `PluginContext` |
| `workflow-progress.json` structure | Undocumented versioning | Internal persistence format |
| `transitions.jsonl` record shape | Stable in practice | Not formally versioned |
| Worker `instructions` field | Ad hoc per worker | Per-category contract pending |
| Cross-plugin automation ids | String references | No manifest dependency declaration |

**Design references:** [`design/011_SKILLS.md`](../design/011_SKILLS.md), [`design/012_CONFIGURATION.md`](../design/012_CONFIGURATION.md), [`design/013_SECURITY.md`](../design/013_SECURITY.md)

---

## Internal APIs (not supported)

The following are implementation details. External plugins and tools must not depend on them.

| Area | Internal symbols (non-exhaustive) |
|------|-----------------------------------|
| Runtime bootstrap | `_build_automation_engine`, `build_ai_service` |
| Plugin platform | `PluginPlatform._activation_errors`, `load_plugin_class`, `validate_manifest` internals |
| Plugin loader | `sys.path` manipulation during import |
| Config | `_from_mapping`, `_read_toml` |
| State machine | `transition_bridge()` multi-hop internals |
| Workflow | `_try_state_transition`, progress JSON layout |
| Dispatch | `_execute_with_worker`, matcher tie-breaking |
| Event bus | `EventBusStats`, subscriber id generation |
| Automation | `_active_rule_chain`, `MAX_AUTOMATION_DEPTH` (value may tune) |
| AI routing | Provider `priority` tie-breaking when config absent |
| Project | `sync_manifest_state`, `_project_manifest_template` |

---

## First-party plugin contracts (reference)

These are **plugin-level** stable identifiers validated by M9–M12. They are not Vedaws core semver APIs but are frozen as reference integrations.

### Git plugin

| Contract | Value |
|----------|-------|
| CLI group | `vedaws git` |
| Worker ids | `git.status`, `git.commit`, `git.push`, … |
| Capabilities | `git-status`, `git-commit`, etc. |

### Software plugin

| Contract | Value |
|----------|-------|
| Template / workflow id | `software` |
| CLI group | `vedaws software` |
| Worker ids | `software.*` |
| Scaffold | `docs/architecture`, `docs/api`, `docs/decisions`, `docs/handoff` |

### Unity plugin

| Contract | Value |
|----------|-------|
| Template / workflow id | `unity` |
| CLI group | `vedaws unity` |
| Worker ids | `unity.*` |
| Scaffold | `Assets/`, `Packages/`, `ProjectSettings/`, `Docs/` |

### Mock AI plugin

| Contract | Value |
|----------|-------|
| Provider id | `mock-ai` |
| Purpose | Validates `AIProvider` SDK without external APIs |

---

## Related documents

| Document | Relationship |
|----------|--------------|
| [`ARCHITECTURE_FREEZE_V0.5.md`](ARCHITECTURE_FREEZE_V0.5.md) | Freeze declaration and change policy |
| [`ARCHITECTURE_REVIEW_V0.5.md`](ARCHITECTURE_REVIEW_V0.5.md) | Audit source for API inventory |
| [`design/README.md`](../design/README.md) | Architecture index |
| [`design/010_PLUGINS.md`](../design/010_PLUGINS.md) | Plugin SDK detail |
| [`design/005_AUTOMATION.md`](../design/005_AUTOMATION.md) | Automation rules detail |
| [`design/017_AI_PROVIDERS.md`](../design/017_AI_PROVIDERS.md) | AI routing detail |

---

**Document status:** Active — v0.5 architecture freeze  
**Code changes:** None (documentation only)
