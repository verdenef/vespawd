# Plugins

**Version:** 0.5.0

**Status:** Active — v0.5 freeze baseline with M14/M16 plugin integration updates

## Purpose

Plugins extend Vedaws at the domain edge without modifying the core runtime. The plugin platform provides discovery, validation, dependency resolution, activation, lifecycle management, and a stable SDK for contributions.

The runtime must never need modification to support new integrations — plugins register capabilities through the SDK.

---

## Architectural Role

Per `002_CORE.md` and `003_RUNTIME.md`:

| Contribution | Status |
|--------------|--------|
| Workers | Implemented |
| Commands | Implemented (generic CLI dispatch) |
| Workflow templates | Registered (installed via project template) |
| Project templates | Implemented (`vedaws init --template`) |
| Skills | Implemented (registered + runtime-consumable metadata) |
| Health checks | Implemented (`vedaws doctor`) |
| Event subscriptions | Implemented (`subscribe_event`) |
| Automation rules | Implemented (`contribute_automation_rule`) |
| AI providers | Implemented (`contribute_ai_provider`) |
| Configuration schema | Implemented (merged and validated during runtime bootstrap) |

**Invariants:**

- Plugins extend the runtime; they do not replace it.
- Core orchestration invariants hold regardless of active plugins.
- Plugin deactivation must not corrupt project state.
- Domain-specific behavior belongs in plugins, not in the core.

---

## Plugin Lifecycle

Lifecycle states are explicit and tracked per plugin record:

```
DISCOVER → VALIDATE → LOAD → INITIALIZE → ACTIVE → UNLOAD
                ↓                              ↓
             FAILED                        DISABLED
```

| State | Meaning |
|-------|---------|
| `discovered` | Manifest found on a search path |
| `validated` | Manifest schema and compatibility checks passed |
| `loaded` | Entry-point module imported |
| `initialized` | `on_load()` completed |
| `active` | `register()` completed; contributions merged |
| `unloaded` | `on_unload()` called during shutdown |
| `disabled` | Listed in activation `disabled` or not in explicit `enabled` |
| `failed` | Validation, load, init, or activation error |

Orchestration: `PluginPlatform` in `runtime/vedaws/plugins/platform.py`.

---

## Manifest v1 (`vedaws.plugin.toml`)

Canonical manifest format — provider-neutral:

```toml
[plugin]
id = "hello"
name = "Hello Plugin"
version = "0.1.0"
author = "Vedaws"
description = "Reference plugin"
manifest_version = "1"
entry_point = "hello_plugin:HelloPlugin"

[plugin.compatibility]
vedaws = ">=0.1.0"
python = ">=3.11"

[capabilities]
workers = true
commands = true
workflows = true
skills = true
health_checks = true
configuration = true

[[dependencies]]
id = "other-plugin"
version = ">=1.0.0"
```

### Required fields

| Field | Description |
|-------|-------------|
| `id` | Unique plugin identifier |
| `name` | Human-readable name |
| `version` | Semver plugin version |
| `entry_point` | `module:Class` relative to plugin root |
| `manifest_version` | Manifest schema version (`1`) |

### Optional fields

| Field | Description |
|-------|-------------|
| `author` | Plugin author |
| `description` | Short description |
| `compatibility.vedaws` | PEP 440 constraint on Vedaws runtime |
| `compatibility.python` | Python version constraint |
| `capabilities.*` | Declared contribution types (documentation) |
| `dependencies` | Other plugin ids with version constraints |
| `security.permissions` | Declared security permissions (`filesystem.*`, `subprocess.exec`, `network.outbound`) |
| `security.subprocess_allow` | Optional command allow-list for subprocess use |
| `security.network` | Declared network posture (`none` or `outbound`) |

### Security declaration (M14)

`vedaws.plugin.toml` may include:

```toml
[security]
permissions = ["filesystem.read", "filesystem.write", "subprocess.exec"]
subprocess_allow = ["git"]
network = "none"
```

These declarations are validated during plugin manifest validation and checked by `vedaws doctor`. They are diagnostic and policy metadata in M14, not hard sandbox enforcement.

---

## Discovery

Plugins are discovered from `vedaws.plugin.toml` in configured search paths (first wins on duplicate id):

1. `~/.vedaws/plugins/`
2. `<install-root>/plugins/`
3. `<project>/.vedaws/plugins/` (when present)
4. Paths from `VEDAWS_PLUGIN_PATHS`

Discovery returns valid manifests, invalid paths, and duplicate id conflicts.

---

## Activation

Activation is separate from discovery. A discovered plugin is not active unless enabled.

### Global activation

`~/.vedaws/plugins.toml`:

```toml
[plugins]
enabled = []
disabled = []
```

### Per-project activation

`.vedaws/plugins.toml` (created by `vedaws init`):

```toml
[plugins]
enabled = ["hello"]
disabled = []
```

### Merge rules

1. `disabled` is the union of global and project lists.
2. If project `enabled` is non-empty, it defines the explicit allow-list.
3. Else if global `enabled` is non-empty, global list applies.
4. Else all discovered plugins are candidates except those disabled.

`vedaws plugins enable|disable` updates the appropriate activation file.

### Future: remote plugins

Manifest and activation formats are provider-neutral. Remote plugin sources (registry URLs, signed bundles) are reserved for a future milestone — discovery paths remain the extension point.

---

## Dependency Resolution

Before activation, `resolve_dependencies()` validates:

- Missing dependencies
- Version compatibility (PEP 440)
- Circular dependencies

Failures are reported gracefully; affected plugins enter `failed` status with error messages. Resolution order is topological (dependencies first).

---

## Plugin SDK

### Base class

```python
from vedaws.plugins.sdk import VedawsPlugin, PluginContext

class MyPlugin(VedawsPlugin):
    def register(self, context: PluginContext) -> None:
        context.contribute_worker(MyWorker())
        context.contribute_health_check(my_check)

    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
```

### Contribution methods (`PluginContext`)

| Method | Registers |
|--------|-----------|
| `contribute_worker(worker)` | `Worker` in `WorkerRegistry` |
| `contribute_command(name, description, group=..., handler=...)` | CLI command group/subcommand |
| `contribute_workflow_template(path)` | Workflow template path |
| `contribute_project_template(id, name, path, description=...)` | Project template for `vedaws init` |
| `contribute_skill(id, name, description)` | Skill metadata |
| `contribute_health_check(callable)` | `vedaws doctor` check |
| `contribute_configuration(schema)` | Configuration schema fragment |
| `contribute_automation_rule(rule)` | Event-driven automation rule |
| `contribute_ai_provider(provider)` | AI provider implementation |
| `subscribe_event(event_type, handler, name=...)` | Event Bus subscription (SDK only) |

Plugins must not modify runtime internals directly — only through `PluginContext`. Plugins must **never** access `EventBus` directly.

### Event subscriptions (Milestone 8)

Plugins observe runtime activity through the public SDK:

```python
from vedaws.events.types import EventType

context.subscribe_event(
    EventType.PROJECT_STATE_CHANGED,
    self._on_state_changed,
    name="state-observer",
)
```

Subscriptions are registered after `register()` completes. Duplicate `(plugin, name)` subscriptions replace prior handlers. Subscriptions are removed on plugin unload.

Example subscriber: Hello plugin (`plugins/hello/`) logs `ProjectStateChanged` events.

### Automation rules (Milestone 11)

Plugins contribute data-driven rules executed by the runtime `AutomationEngine`:

```python
from vedaws.automation.model import AutomationRule, RuleAction, RuleCondition
from vedaws.events.types import EventType

context.contribute_automation_rule(
    AutomationRule(
        id="software.implement-git-status",
        on_event=EventType.TASK_COMPLETED,
        conditions=RuleCondition.from_mapping({"task_id": "implement"}),
        actions=(RuleAction(type="execute_worker", params={"worker_id": "git.status"}),),
    )
)
```

Project-local rules and enable/disable overrides live in `.vedaws/automation.toml`. See `005_AUTOMATION.md`.

### AI providers (Milestone 12)

Plugins contribute provider implementations:

```python
from vedaws.ai.provider import AIProvider

context.contribute_ai_provider(MockAIProvider())
```

Routing configuration lives in `.vedaws/config.toml` under `[ai]`. See `017_AI_PROVIDERS.md`.

### Project templates (Milestone 9)

Plugins ship a `templates/project/` directory:

```
templates/project/
  template.toml          # id, name, scaffold_dir, default_workflow, plugins.enabled
  workflows/*.workflow.toml
  scaffold/              # copied to project root on init
```

Discovery scans discovered plugin paths — **activation not required** for `vedaws init --template`.

```python
context.contribute_project_template(
    "software",
    "Software Development",
    template_root,
    description="Software lifecycle workflow with standard artifacts",
)
```

CLI:

```bash
vedaws init --list-templates
vedaws init --template software [path]
vedaws init software    # template id shorthand (initializes cwd)
vedaws init --template unity [path]
vedaws init unity       # Unity game template shorthand
```

Reference domain plugins: `plugins/software/` (PAWS successor), `plugins/unity/` (game development validation).

### Command groups

Plugins register CLI commands via `contribute_command`. Use `group` for nested commands:

```python
context.contribute_command(
    "status",
    "Show repository status",
    group="git",
    handler=my_handler,
)
```

This registers `vedaws git status`. Commands without `group` become top-level `vedaws <name>` parsers.

The runtime discovers commands through `collect_plugin_command_groups()` and registers argparse parsers dynamically in `cli/plugin_commands.py`. **No domain-specific commands are hardcoded in the runtime.**

Handlers receive `argparse.Namespace` with at least `path` (workspace). Subcommand-specific flags are added by the generic registrar where applicable.

---

## Bootstrap Integration

```
load_config → setup_logging
  → EventBus (runtime-owned)
  → discover_workers → WorkerRegistry (+ WorkerRegistered events)
  → register_mock_workers
  → PluginPlatform (discover → validate → activate, PluginLoaded events)
  → detect_project → wire state/workflow publishers
  → WorkerDispatcher (+ WorkerStarted/Completed events)
```

Active plugin workers are merged into the same `WorkerRegistry` as built-in workers. Mock workers still override manifest-only entries with the same id.

---

## CLI

| Command | Description |
|---------|-------------|
| `vedaws plugins` | List discovered plugins and status |
| `vedaws plugins list` | Same as above |
| `vedaws plugins info <id>` | Manifest, lifecycle, contributions |
| `vedaws plugins enable <id>` | Enable in project (or `--global`) |
| `vedaws plugins disable <id>` | Disable in project (or `--global`) |
| `vedaws events` | Event types, subscriber counts, publish statistics |
| `vedaws automation list` | Automation rules registered for the project |
| `vedaws automation enable\|disable <id>` | Per-rule enable overrides |
| `vedaws automation run` | Manually trigger rule(s) |
| `vedaws ai providers` | List AI provider plugins |
| `vedaws ai capabilities` | Capability routing map |
| `vedaws ai status` | AI platform health |

Plugin-contributed commands are registered automatically when active (e.g. `vedaws git status` from the Git plugin).

---

## Diagnostics

`vedaws doctor` validates:

- Plugin registry (discovery count, active count)
- Plugin platform (invalid manifests, duplicates, failed activations, dependency errors)
- Plugin health checks (from active plugins' `contribute_health_check`)
- Plugin security declarations (invalid permissions, subprocess/network policy issues)
- Event bus (initialized, subscriber registry healthy)

---

## Reference Plugins

### Software (`plugins/software/`) — domain reference (Milestone 9)

First domain plugin — software development lifecycle (PAWS successor). See `008_ARTIFACTS.md`, `011_SKILLS.md`, `docs/MILESTONE_9_SUMMARY.md`.

### Unity (`plugins/unity/`) — multi-domain validation (Milestone 10)

Second domain plugin — Unity game development lifecycle. Proves Vedaws is a Development Operating System, not a software-only framework. No Unity Editor, MCP, or AI integration. See `008_ARTIFACTS.md`, `011_SKILLS.md`, `docs/MILESTONE_10_SUMMARY.md`.

| Capability | CLI | Worker id | Task capability |
|------------|-----|-----------|-----------------|
| Layout & artifacts | `vedaws unity status` | — | — |
| Workflow summary | `vedaws unity workflow` | — | — |
| Build stub | `vedaws unity build [--target]` | `unity.build` | `unity-build` |
| Package manifest | `vedaws unity package` | `unity.package` | `unity-release` |
| Concept / design | — | `unity.design` | `unity-concept`, `unity-game-design` |
| Scenes / UI | — | `unity.scene` | `unity-prototype`, `unity-ui` |
| Prefabs / scripts | — | `unity.prefab`, `unity.script` | `unity-gameplay` |
| Testing | — | `unity.test` | `unity-testing` |

### Hello (`plugins/hello/`)

Minimal platform example — worker, health check, templates, skill, configuration, event subscriber.

### Git (`plugins/git/`) — production reference

First-party plugin validating the platform. All Git logic lives in the plugin; the runtime has no Git-specific code.

| Capability | CLI | Worker id | Task capability |
|------------|-----|-----------|-----------------|
| Repository status | `vedaws git status` | `git.status` | `git-status` |
| Current / create branch | `vedaws git branch [--create NAME]` | `git.branch` | `git-branch` |
| Stage + commit | `vedaws git commit -m MSG [--stage-all]` | `git.commit` | `git-commit` |
| Fetch | `vedaws git fetch [--remote]` | `git.fetch` | `git-fetch` |
| Pull | `vedaws git pull [--remote]` | `git.pull` | `git-pull` |
| Push | `vedaws git push [--remote]` | `git.push` | `git-push` |

**Error handling** (plugin-local, not runtime):

- `GitNotInstalledError` — git executable missing
- `NotARepositoryError` — workspace not a repository
- `DetachedHeadError` — branch operations on detached HEAD
- `MergeConflictError` — pull/merge conflicts
- `GitAuthError` — push authentication unavailable (stub/warn)

**Doctor checks** contributed by the Git plugin:

- `git installation` — executable on PATH
- `git plugin` — plugin active
- `git workers` — workers registered
- `git repository` — repository detected at workspace

---

## v0.5 freeze limitations

| Item | Notes |
|------|-------|
| Workflow/project template install | Project templates install workflows + scaffold; standalone workflow install deferred |
| Skill runtime binding | First runtime consumer implemented in M16 (`AIExecutableWorker`) |
| Configuration merge | `contribute_configuration` merged/validated in M16 bootstrap flow |
| Remote plugin sources | Activation format ready; fetch/install not implemented |
| Plugin sandboxing | Trust-all local plugins; no isolation (`013_SECURITY.md`, post-M14 gap) |
| Permission enforcement | Manifest + doctor checks only; no OS-level sandbox |
| Hot reload | Requires runtime restart to pick up plugin changes |
| Event bus publish from SDK | `subscribe_event` only; no plugin `publish` API |
| Plugin command custom args | Generic registrar covers common flags; complex CLIs need SDK extension |
| Hello reference plugin | `vedaws hello` registered without handler (review technical debt) |

---

## Public APIs

| Symbol | Package |
|--------|---------|
| `VedawsPlugin`, `PluginContext` | `vedaws.plugins.sdk` |
| `PluginManifest`, `PluginDependency` | `vedaws.plugins.manifest` |
| `PluginStatus` | `vedaws.plugins.lifecycle` |
| `PluginContributions`, `PluginCommand` | `vedaws.plugins.contributions` |
| `collect_plugin_command_groups` | `vedaws.plugins.commands` |
| `Event`, `EventBus`, `EventType`, `create_event` | `vedaws.events` |
| `PluginRegistry`, `PluginRecord` | `vedaws.plugins.registry` |
| `PluginPlatform` | `vedaws.plugins.platform` |
| `discover_plugins` | `vedaws.plugins.discovery` |
| `resolve_dependencies` | `vedaws.plugins.dependencies` |
| `AutomationRule`, `RuleAction`, `RuleCondition` | `vedaws.automation.model` |
| `contribute_automation_rule` | `vedaws.plugins.sdk.PluginContext` |
| `AIProvider` | `vedaws.ai.provider` |
| `ChatRequest`, `ChatResponse`, `GenerateRequest`, `GenerateResponse` | `vedaws.ai.model` |
| `STANDARD_AI_CAPABILITIES` | `vedaws.ai.capabilities` |
| `contribute_ai_provider` | `vedaws.plugins.sdk.PluginContext` |
| `AIService` | `vedaws.ai.service` (runtime facade on `RuntimeContext`) |

---

## TODO (post-freeze)

- Auto-install workflow templates on project init or `workflow install`
- Extend plugin configuration schema validation depth (nested object support)
- Extensible per-command argparse registration in SDK
- Remote plugin registry and signed bundles
- Plugin sandbox and permission model (`013_SECURITY.md`, M14)
- Complete hello plugin command handler (reference quality)
