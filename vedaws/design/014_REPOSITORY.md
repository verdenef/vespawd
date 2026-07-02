# Repository

**Version:** 0.5.0

**Status:** Active — Vedaws monorepo layout at v0.5 freeze

## Purpose

This document describes the **Vedaws source repository layout** — how the DevOS kernel, plugins, tests, and design artifacts are organized on disk.

It is distinct from the **project layout** under `.vedaws/` in a user's workspace, which is defined in `007_PROJECT_MODEL.md`.

---

## Monorepo root

```
vedaws/
├── design/                 # Canonical architecture documents (source of truth)
├── docs/                   # Milestone summaries, architecture review, freeze artifacts
├── runtime/                # Python package root (setuptools finds vedaws here)
│   └── vedaws/             # Core runtime implementation
├── plugins/                # First-party plugin packages
├── tests/                  # Integration and unit tests
├── workers/                # Standalone worker manifest examples (discovery targets)
├── examples/               # Sample workspaces (e.g. sprint1-demo)
├── skills/                 # Reserved; empty at v0.5 (skills live in plugins)
├── automation/             # Reserved; empty at v0.5 (rules live in .vedaws/ and plugins)
├── templates/              # Reserved; project templates live in plugins/
├── scripts/                # Reserved for tooling scripts
├── .ai/                    # Architecture escalation rules
├── .cursor/                # Editor rules
├── pyproject.toml          # Package metadata and entry point (vedaws CLI)
└── VEDAWS_BOOTSTRAP.md     # Package readme (legacy bootstrap name)
```

---

## Runtime package (`runtime/vedaws/`)

Domain-neutral orchestration only. No software, Unity, Git, or vendor AI logic in core.

| Package | Responsibility |
|---------|----------------|
| `runtime/` | Bootstrap, `RuntimeContext`, lifecycle |
| `cli/` | Command-line interface |
| `config/` | Layered configuration loading |
| `project/` | Project detection, init, templates, state machine |
| `workflow/` | Workflow engine and task registry |
| `workers/` | Worker registry, discovery, execution models |
| `dispatch/` | Worker dispatcher and matcher |
| `events/` | In-process event bus |
| `plugins/` | Plugin platform (discovery, SDK, lifecycle) |
| `automation/` | Automation engine (M11) |
| `ai/` | AI provider SDK and routing (M12) |
| `doctor/` | Health checks |
| `logging/` | Logging setup |
| `status/` | Status reporters |

See `003_RUNTIME.md` and [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md) for the orchestration layer diagram.

---

## Plugins (`plugins/`)

Each plugin is a self-contained package with `vedaws.plugin.toml` at its root.

| Plugin | Directory | Role at v0.5 |
|--------|-----------|--------------|
| `hello` | `plugins/hello/` | Minimal reference plugin |
| `git` | `plugins/git/` | Real external tool integration (Git) |
| `software` | `plugins/software/` | Software development domain template + workflow |
| `unity` | `plugins/unity/` | Unity game development domain template + workflow |
| `mock-ai` | `plugins/mock-ai/` | Reference AI provider (no external APIs) |

Typical plugin layout:

```
plugins/<name>/
├── vedaws.plugin.toml      # Manifest v1
├── <name>_plugin/          # Python package (entry_point target)
│   └── __init__.py         # VedawsPlugin subclass
├── templates/              # Optional: project and workflow templates
└── tests/                  # Optional: plugin-local tests (if present)
```

Plugin discovery searches configured paths (`012_CONFIGURATION.md`). First-party plugins ship in `plugins/` adjacent to the runtime.

---

## Worker manifests (`workers/`)

Standalone `vedaws.worker.toml` examples for manifest-based worker discovery. Includes mock workers (`workers/mock/`) and placeholder manifests for tools and AI (`workers/tool/`, `workers/ai/`, `workers/human/`).

Executable workers are primarily registered via **plugins** at v0.5; manifest workers supplement discovery and testing (`004_WORKERS.md`).

---

## Tests (`tests/`)

Integration tests for runtime, CLI, plugins, workflow, state, dispatch, events, automation, and AI. **107 tests** at architecture review time (`ARCHITECTURE_REVIEW_V0.5.md`).

Test layout mirrors subsystems: `test_plugins.py`, `test_automation.py`, `test_ai_providers.py`, domain plugin tests, etc.

---

## Design and documentation

| Path | Role |
|------|------|
| `design/` | Architecture specifications (`000`–`017`); see `design/README.md` |
| `docs/` | Milestone summaries (M6–M12), `ARCHITECTURE_REVIEW_V0.5.md`, `ARCHITECTURE_FREEZE_V0.5.md`, `API_STABILITY.md` |
| `.ai/architect_escalation.md` | When to stop for architecture review |

---

## User workspace vs repository

| Location | What it is |
|----------|------------|
| **This repository** | Vedaws product source — runtime + first-party plugins |
| **`<project>/.vedaws/`** | Per-project orchestration data on a user's machine |
| **`~/.vedaws/`** | Per-user Vedaws config and global plugin activation |

A developer clones or installs Vedaws from the monorepo, then runs `vedaws init` in a separate workspace to create a project. Project layout is **not** a subtree of this repository unless explicitly copied (e.g. `examples/sprint1-demo/`).

---

## Reserved / scaffold directories

These directories exist from initial repository bootstrap. At v0.5 freeze they are **empty or placeholder** — active implementations live elsewhere:

| Directory | Active location at v0.5 |
|-----------|-------------------------|
| `skills/` | Plugin `contribute_skill()` metadata (`011_SKILLS.md`) |
| `automation/` | `.vedaws/automation.toml` + plugin rules (`005_AUTOMATION.md`) |
| `templates/` | `plugins/*/templates/` (`010_PLUGINS.md`) |
| `scripts/` | No required scripts yet |

Do not assume root-level `skills/` or `automation/` directories are loaded by the runtime.

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `007_PROJECT_MODEL.md` | On-disk **project** layout (`.vedaws/`) |
| `010_PLUGINS.md` | Plugin package conventions and SDK |
| `004_WORKERS.md` | Worker discovery paths including `workers/` |
| `016_IMPLEMENTATION_PLAN.md` | Milestone delivery against this layout |

---

## TODO

- Document release/tag layout when package version aligns to `0.5.0`
- Add `scripts/` entries when CI or release tooling lands
- Revisit reserved directories if central `skills/` or `automation/` registries are introduced (requires architecture review)
