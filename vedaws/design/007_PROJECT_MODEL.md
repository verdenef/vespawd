# Project Model

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (templates M9–10, automation M11, `[ai]` config M12)

## Purpose

This document describes how a Vedaws **project** is represented on disk and loaded at runtime. It specializes the Project concept from `002_CORE.md` for the current implementation.

---

## Project Root

A Vedaws project is detected by the presence of:

```
<workspace>/.vedaws/project.toml
```

The directory containing `.vedaws/` is the **project root**. Configuration and orchestration data live under `.vedaws/`.

---

## Directory Layout

```
.vedaws/
├── project.toml              # Human-readable manifest (name, mirrored state, template)
├── config.toml               # Project-local Vedaws configuration (includes [ai] routing, M12)
├── plugins.toml              # Per-project plugin activation
├── state.toml                # Authoritative current project state
├── transitions.jsonl         # Append-only state transition history
├── workflow-progress.json    # Workflow and task runtime progress
├── automation.toml           # Event-driven automation rules (Milestone 11)
└── workflows/
    └── *.workflow.toml       # Workflow definitions
```

**Software template** projects additionally include plugin-scaffolded paths at the project root (see `008_ARTIFACTS.md`):

```
docs/
├── architecture/
├── api/
├── decisions/
└── handoff/
```

**Unity template** projects scaffold a Unity-style layout (see `008_ARTIFACTS.md`):

```
Assets/
Packages/
ProjectSettings/
Docs/
├── game-design/
├── technical-design/
├── builds/
└── playtests/
```

Optional future paths:

```
.vedaws/plugins/              # Project-scoped plugin manifests
.vedaws/workers/              # Project-scoped worker manifests
```

---

## Manifest (`project.toml`)

```toml
[project]
name = "my-project"
state = "created"   # Mirror of state.toml — not authoritative
template = "software"   # Optional — set when a plugin template was applied
# template = "unity"
```

**Authoritative state** is always `state.toml`. The `state` field in `project.toml` is synchronized by the runtime after transitions for human readability.

---

## Project Templates (Milestone 9)

Plugins contribute project templates via `templates/project/template.toml` under the plugin root. The runtime discovers templates without requiring plugin activation (for `vedaws init`).

```bash
vedaws init --list-templates
vedaws init --template software [path]
vedaws init software              # shorthand: template id, init in cwd
vedaws init --template unity [path]
vedaws init unity                 # Unity game template shorthand
```

Generic application (`project/templates.py`):

1. Base init (manifest, state, config, plugins.toml)
2. Remove default workflow if template requests it
3. Copy `workflows/*.workflow.toml` into `.vedaws/workflows/`
4. Copy `scaffold/**` to project root
5. Merge template plugin activation list into `plugins.toml`
6. Record `template` in `project.toml`

---

## Project Context

At runtime, `ProjectContext` aggregates:

| Field | Type | Role |
|-------|------|------|
| `root` | Path | Project root directory |
| `name` | str | From `project.toml` |
| `state_engine` | `StateEngine` | Canonical lifecycle state |
| `workflow_engine` | `WorkflowEngine` | Workflows, tasks, progress |

Loaded by `detect_project()` during bootstrap.

**M15 update:** project detection supports read-only mode to avoid write-on-read side effects during bootstrap and diagnostics. Manifest synchronization remains explicit and separate from detection.

---

## Lifecycle

Operational states are defined in `006_STATE_MACHINE.md`. Project initialization (`vedaws init`) creates:

1. `project.toml`, `config.toml`, `plugins.toml`
2. `state.toml` at `created`
3. Initial history entry in `transitions.jsonl`
4. Default workflow **or** plugin template workflow(s)

---

## Invariants

- Every orchestration action requires a detected `ProjectContext`.
- State in `state.toml` overrides `project.toml` on conflict.
- Workflow progress is scoped to the project directory.
- Projects do not share `.vedaws/` data unless explicitly copied.
- Domain-specific project layouts come from plugins, not the runtime core.

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `002_CORE.md` | Conceptual Project definition |
| `006_STATE_MACHINE.md` | Operational state machine |
| `008_ARTIFACTS.md` | Software and Unity artifact paths |
| `010_PLUGINS.md` | Project template contribution |
| `012_CONFIGURATION.md` | Project `config.toml` layering (`[ai]` routing) |
| `005_AUTOMATION.md` | `automation.toml` rules |
| `017_AI_PROVIDERS.md` | `[ai]` section in project config |

---

## TODO

- Schema versioning and migrations for `.vedaws/` formats — deferred (review P2).
- Template dependency ordering when multiple plugins contribute templates.
- Evaluate whether manifest mirror sync should be CLI-command scoped instead of bootstrap scoped.
