# Sprint 4 Summary — Workflow & Task Engine

**Status:** Complete  
**Version:** 0.1.0

Sprint 4 implements the workflow and task engine — Vedaws' model for understanding what work needs to be done. Workflows are defined, loaded, activated, and tracked. Task lifecycle is modeled and persisted. Workflow progress integrates with the Project State Engine via `workflow_rule` transitions. Workers do not execute tasks yet.

---

## 1. Repository Tree

```
vedaws/
├── pyproject.toml
├── VEDAWS_BOOTSTRAP.md
│
├── design/                         # Architecture documents (000–016)
│   └── 006_STATE_MACHINE.md        # Updated 0.2.0 — aligned with Sprint 3 states
│
├── runtime/vedaws/                 # Python package
│   ├── cli/
│   │   └── commands.py             # + vedaws workflow, vedaws tasks
│   │
│   ├── config/
│   │   └── paths.py                # + workflows dir, progress file constants
│   │
│   ├── doctor/
│   │   └── checks.py               # + workflow definition health check
│   │
│   ├── project/
│   │   ├── detector.py             # loads WorkflowEngine with StateEngine
│   │   ├── init.py                 # creates default.workflow.toml on init
│   │   └── model.py                # ProjectContext + workflow_engine
│   │
│   ├── status/
│   │   └── reporter.py             # shows workflow/task summary
│   │
│   └── workflow/                   # Sprint 4 — Workflow & Task Engine
│       ├── states.py               # WorkflowStatus, TaskStatus enums
│       ├── models.py               # WorkflowDefinition, TaskDefinition, instances
│       ├── manifest.py             # *.workflow.toml parsing
│       ├── loader.py               # discover and load workflow definitions
│       ├── persistence.py          # workflow-progress.json
│       ├── registry.py             # TaskRegistry
│       ├── tracker.py              # progress derivation, readiness evaluation
│       ├── engine.py               # WorkflowEngine + state integration
│       └── reporter.py             # CLI formatting
│
├── tests/
│   ├── test_workflow.py            # NEW — workflow engine tests
│   └── test_cli.py                 # + workflow/tasks CLI tests
│
└── docs/
    ├── SPRINT_3_SUMMARY.md
    └── SPRINT_4_SUMMARY.md
```

### Per-project files (`.vedaws/`)

| File | Purpose |
|------|---------|
| `workflows/*.workflow.toml` | Workflow definitions (tasks, dependencies, capabilities) |
| `workflow-progress.json` | Authoritative workflow and task runtime state |

---

## 2. Architecture Summary

### Layering

```
CLI (workflow, tasks)
        │
        ▼
WorkflowEngine ─────────────► StateEngine
        │                     (TransitionTrigger.WORKFLOW_RULE)
        ├── WorkflowLoader
        ├── TaskRegistry
        ├── ProgressTracker
        └── Persistence (workflow-progress.json)
```

### Workflow definitions

Workflows live in `.vedaws/workflows/` as `*.workflow.toml` files. Each manifest declares a `[workflow]` section and a `[[tasks]]` array. Tasks may declare `depends_on`, `capability`, and `requires_approval` for future worker dispatch and approval gates.

On `vedaws init`, a **default workflow** with three tasks (`plan` → `validate` → `ready`) is created.

### Task lifecycle (modeled, not executed)

| Status | Meaning |
|--------|---------|
| `defined` | Task exists in definition; workflow not yet active |
| `pending` | Workflow active; dependencies not satisfied |
| `ready` | Dependencies met; eligible for dispatch (Sprint 5) |
| `dispatched` | Assigned to a worker (Sprint 5) |
| `running` | Worker executing (Sprint 5) |
| `completed` | Successful outcome recorded |
| `failed` | Failure recorded |
| `cancelled` | Explicitly cancelled |
| `recorded` | Outcome persisted; effects applied or queued |

Sprint 4 supports manual `tasks complete` and `tasks fail` from **ready** status only — simulating outcomes without workers.

### Workflow lifecycle

| Status | Meaning |
|--------|---------|
| `defined` | Structure exists, not active |
| `activated` | Workflow in effect; tasks initialized |
| `in_progress` | At least one task pending, ready, dispatched, or running |
| `blocked` | A task failed or progress halted |
| `completed` | All required tasks completed/recorded |
| `cancelled` | Terminated before completion |

Workflow status is **derived** from task states via `tracker.py`; it is not set independently.

### Project state integration

`WorkflowEngine` holds a reference to `StateEngine` and drives transitions via `TransitionTrigger.WORKFLOW_RULE`:

| Event | Typical project state |
|-------|----------------------|
| Workflow activated | `planning` (or `ready` if tasks immediately ready) |
| Tasks ready | `ready` |
| Work in flight | `executing` |
| Task failed | `failed` (via bridge through `executing` when needed) |
| All tasks done | `completed` |
| Approval-required task completes | `awaiting_approval` |

Bridge transitions handle cases where the canonical state machine requires intermediate states (e.g. `ready` → `executing` → `failed`).

### Design for Sprint 5

- `TaskDefinition.capability` maps to worker capability matching.
- `TaskStatus.READY` is the dispatch eligibility gate.
- `TaskStatus.DISPATCHED` / `RUNNING` reserved for worker execution.
- `requires_approval` flag routes to `awaiting_approval` on completion.

---

## 3. Public APIs

### Package: `vedaws.workflow`

```python
from vedaws.workflow import (
    WorkflowEngine,
    WorkflowDefinition,
    TaskDefinition,
    WorkflowInstance,
    TaskInstance,
    TaskRegistry,
    WorkflowStatus,
    TaskStatus,
    WorkflowProgress,
    WorkflowError,
    WorkflowNotFoundError,
    TaskNotFoundError,
    InvalidTaskTransitionError,
    load_workflow_definitions,
    parse_task_ref,
    compute_progress,
)
```

### `WorkflowEngine`

| Method | Description |
|--------|-------------|
| `WorkflowEngine.load(project_dir, state_engine=None)` | Load definitions, restore progress, wire state engine |
| `list_workflows()` | All loaded workflow definitions |
| `get_workflow(id)` | Lookup definition by id |
| `get_workflow_instance(id)` | Runtime workflow instance |
| `progress(id)` | `WorkflowProgress` snapshot |
| `activate(id)` | Activate workflow, init tasks, sync project state |
| `complete_task(workflow_id, task_id)` | Record success (ready → completed → recorded) |
| `fail_task(workflow_id, task_id)` | Record failure, mark workflow blocked |
| `task_registry` | `TaskRegistry` with definitions and instances |

### `TaskRegistry`

| Method | Description |
|--------|-------------|
| `register_workflow(definition)` | Index task definitions from a workflow |
| `get_definition(workflow_id, task_id)` | Task definition lookup |
| `get_instance(workflow_id, task_id)` | Task instance lookup |
| `ensure_instance(workflow_id, task_id)` | Get or create instance |
| `list_for_workflow(workflow_id)` | All task instances for a workflow |
| `list_ready()` | Tasks in ready status |

### `ProjectContext` (extended)

```python
@dataclass
class ProjectContext:
    root: Path
    name: str
    state_engine: StateEngine
    workflow_engine: WorkflowEngine | None = None
```

Loaded automatically by `detect_project()` during bootstrap.

### CLI

```bash
vedaws workflow [-C path]                    # List workflows and progress
vedaws workflow show <id> [-C path]          # Workflow detail
vedaws workflow activate <id> [-C path]      # Activate workflow

vedaws tasks [-C path]                       # List all tasks
vedaws tasks show <workflow.task> [-C path]  # Task detail
vedaws tasks complete <workflow.task>        # Record success (no worker)
vedaws tasks fail <workflow.task>            # Record failure (no worker)
```

### Workflow manifest format

```toml
[workflow]
id = "default"
name = "Default workflow"
version = "0.1.0"
description = "Optional description"

[[tasks]]
id = "plan"
name = "Plan work"
capability = "planning"

[[tasks]]
id = "validate"
name = "Validate setup"
depends_on = ["plan"]
capability = "validation"
requires_approval = false
```

---

## 4. Directory Structure

```
runtime/vedaws/workflow/
├── __init__.py          # Public exports
├── states.py            # WorkflowStatus, TaskStatus
├── models.py            # Definition and instance dataclasses
├── manifest.py          # TOML parsing
├── loader.py            # Filesystem discovery
├── persistence.py       # workflow-progress.json read/write
├── registry.py          # TaskRegistry
├── tracker.py           # Progress + dependency readiness
├── engine.py            # WorkflowEngine orchestration
└── reporter.py          # CLI output formatting
```

### Persistence schema (`workflow-progress.json`)

```json
{
  "workflows": {
    "default": {
      "workflow_id": "default",
      "status": "in_progress",
      "activated_at": "2026-06-30T12:00:00+00:00",
      "updated_at": "2026-06-30T12:00:00+00:00"
    }
  },
  "tasks": {
    "default.plan": {
      "workflow_id": "default",
      "task_id": "plan",
      "status": "recorded",
      "updated_at": "2026-06-30T12:00:01+00:00"
    }
  }
}
```

---

## Tests

**38 tests passing** (9 new workflow tests + 2 CLI tests).

Key coverage:
- Default workflow created on init
- Definition loading and registry
- Workflow activation and task readiness
- Dependency chain advancement on complete
- Workflow completion and failure paths
- Progress persistence across reload
- Project state sync via workflow rules
- CLI workflow/tasks commands

---

## Non-goals (deferred)

| Area | Sprint |
|------|--------|
| Worker task execution | Sprint 5 |
| AI, automation, scheduling | Later |
| MCP, Unity, Git integration | Later |

---

## Next: Sprint 5

Worker execution will:
- Dispatch `ready` tasks to workers by capability
- Transition tasks through `dispatched` → `running` → `completed`/`failed`
- Replace manual `tasks complete`/`fail` for normal operation
