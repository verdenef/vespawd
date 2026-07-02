# Vedaws

**A domain-neutral Development Operating System (DevOS)**

Vedaws orchestrates project state, workflows, workers, automation, and AI capabilities — without embedding domain logic in the core runtime. Domain behavior (software, Unity, Git, AI providers) ships as plugins.

> Orchestrate work. Not just code.

**Architecture version:** 0.5.0 (frozen at Milestone 12)  
**Package version:** 0.5.0  
**Status:** Architecture proof — not v1 production-ready

---

## What Vedaws does today

Through Milestone 16, Vedaws provides:

- **Project orchestration** — `.vedaws/` state, workflows, and task dispatch
- **Plugin platform** — discovery, lifecycle, SDK contributions
- **Event bus** — synchronous in-process coordination
- **Automation engine** — event-driven rules (`on_event` → `if` → `then`)
- **AI provider SDK** — capability-based routing (`chat`, `plan`, `implement`, …) via plugins
- **First-party plugins** — `git`, `software`, `unity`, `mock-ai`

121 integration tests in the current baseline.

---

## Requirements

- Python **3.11+**
- Git on PATH (for the Git plugin)

---

## Install (from source)

```bash
git clone <repository-url>
cd vedaws
pip install -e ".[dev]"
```

Verify:

```bash
vedaws version
vedaws --help
```

---

## Quick start

Initialize a project in an empty directory:

```bash
mkdir my-project && cd my-project
vedaws init --name my-project
vedaws doctor
vedaws status
```

Initialize with a domain template:

```bash
vedaws init --name my-app --template software
# or
vedaws init --name my-game --template unity
```

Inspect plugins, automation, and AI routing:

```bash
vedaws plugins list
vedaws automation list
vedaws ai providers
```

Run workflows and dispatch ready tasks (after activating workflows):

```bash
vedaws workflow show
vedaws workflow activate <workflow-id>
vedaws run
```

Path convention (recommended for scripts and multi-repo shells):

```bash
vedaws status --path /path/to/workspace
vedaws doctor --path /path/to/workspace
vedaws run --path /path/to/workspace
```

Plugin commands (examples):

```bash
vedaws git status
vedaws software --help
vedaws unity --help
```

---

## Onboarding workflows

### Author a workflow

1. Create a workflow file under `.vedaws/workflows/`:

```toml
[workflow]
id = "my-flow"
name = "My Flow"

[[tasks]]
id = "plan"
name = "Plan"
capability = "success"
```

2. Activate and inspect:

```bash
vedaws workflow activate my-flow
vedaws tasks
```

### Create a plugin (minimal)

1. Create a plugin package with `vedaws.plugin.toml` and a Python entrypoint.
2. Implement `VedawsPlugin.register()` and contribute workers/commands/templates.

```python
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

class MyPlugin(VedawsPlugin):
    def register(self, context: PluginContext) -> None:
        context.contribute_command("hello", "Example command", group="my")
```

3. Confirm discovery and activation:

```bash
vedaws plugins list
vedaws plugins info <plugin-id>
```

For the complete plugin model, see [`design/010_PLUGINS.md`](design/010_PLUGINS.md).

---

## Core CLI commands

| Command | Purpose |
| ------- | ------- |
| `init` | Create `.vedaws/` project |
| `status` | Runtime and project status |
| `doctor` | Health checks |
| `state` | State history and transitions |
| `workflow` | Workflow inspection and activation |
| `tasks` | Task status and manual outcomes |
| `run` | Dispatch ready workflow tasks |
| `workers` | Worker registry |
| `plugins` | Plugin management |
| `events` | Event bus statistics |
| `automation` | Automation rules |
| `ai` | AI providers and capabilities |

---

## Run tests

```bash
pytest
```

From the repository root with dev dependencies installed.

---

## Documentation

| Document | Purpose |
| -------- | ------- |
| [`design/README.md`](design/README.md) | Architecture index (start here) |
| [`docs/ARCHITECTURE_FREEZE_V0.5.md`](docs/ARCHITECTURE_FREEZE_V0.5.md) | v0.5 freeze declaration |
| [`docs/API_STABILITY.md`](docs/API_STABILITY.md) | Frozen public APIs |
| [`docs/ARCHITECTURE_REVIEW_V0.5.md`](docs/ARCHITECTURE_REVIEW_V0.5.md) | Architecture audit |
| [`design/015_ROADMAP.md`](design/015_ROADMAP.md) | Roadmap toward v1 |
| [`design/014_REPOSITORY.md`](design/014_REPOSITORY.md) | Repository layout |

Milestone summaries: `docs/MILESTONE_6_SUMMARY.md` through `docs/MILESTONE_16_SUMMARY.md`.

---

## Architecture rules (summary)

1. **Domain logic lives in plugins** — not in `runtime/vedaws/`.
2. **`state.toml` is authoritative** — `project.toml` mirrors state only.
3. **Workers match by capability** — not by implementation type.
4. **AI requests use capabilities** — no vendor SDKs in core.
5. **Changes to frozen decisions** require architecture review — see `.ai/architect_escalation.md`.

---

## Known limitations (v0.5)

- AI worker execution remains synchronous; async job/distributed orchestration is still deferred.
- Skill runtime consumption currently has one concrete consumer (`AIExecutableWorker`); broader consumers are future work.
- **Security** is trust-all local plugins — no sandbox (`design/013_SECURITY.md`).
- Event payload typing/schema versioning and `.vedaws` schema migration remain deferred.

Details: [`docs/ARCHITECTURE_FREEZE_V0.5.md`](docs/ARCHITECTURE_FREEZE_V0.5.md).
