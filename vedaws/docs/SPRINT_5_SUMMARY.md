# Sprint 5 Summary — Worker Execution Engine

**Status:** Complete  
**Version:** 0.1.0

Sprint 5 implements Vedaws' first real orchestration capability: the runtime dispatches **READY** tasks to compatible workers, tracks the full execution lifecycle, and propagates outcomes to workflow progress and project state. Mock workers validate the architecture without integrating real AI providers.

---

## 1. Repository Tree

```
vedaws/
├── pyproject.toml
│
├── runtime/vedaws/
│   ├── cli/commands.py              # + vedaws run, vedaws workers run
│   ├── dispatch/                    # NEW — Sprint 5
│   │   ├── dispatcher.py          # WorkerDispatcher
│   │   ├── matcher.py               # Capability matching
│   │   ├── runner.py                # run_until_idle loop
│   │   ├── models.py                # DispatchResult, RunSummary
│   │   └── reporter.py              # CLI formatting
│   │
│   ├── doctor/checks.py             # + dispatcher, execution pipeline checks
│   ├── runtime/
│   │   ├── bootstrap.py             # registers mocks, creates dispatcher
│   │   └── context.py               # + dispatcher field
│   │
│   ├── status/reporter.py           # shows dispatcher status
│   ├── workers/
│   │   ├── execution.py             # TaskDispatch, TaskOutcome
│   │   ├── interface.py             # + ExecutableWorker ABC
│   │   ├── registry.py              # + find_executable_by_capability
│   │   ├── status.py                # + ASSIGNED, EXECUTING
│   │   └── mock/                    # NEW — mock workers
│   │       ├── base.py
│   │       ├── echo.py, sleep.py, success.py, failure.py
│   │       └── registry.py
│   │
│   └── workflow/
│       ├── engine.py                # + dispatch lifecycle methods
│       ├── models.py                # + assigned_worker_id, outcome_message
│       └── persistence.py           # extended task instance fields
│
├── workers/mock/                    # Mock worker manifests
│   ├── echo/vedaws.worker.toml
│   ├── sleep/vedaws.worker.toml
│   ├── success/vedaws.worker.toml
│   └── failure/vedaws.worker.toml
│
├── tests/
│   ├── test_dispatch.py             # NEW
│   ├── test_cli.py                  # + run, workers run tests
│   └── test_bootstrap.py            # dispatcher on project bootstrap
│
└── docs/SPRINT_5_SUMMARY.md
```

---

## 2. Architecture Summary

### Orchestration flow

```
vedaws run
    │
    ▼
run_until_idle(WorkerDispatcher)
    │
    ├── list READY tasks (TaskRegistry)
    ├── match capability → ExecutableWorker (matcher)
    ├── READY → DISPATCHED → RUNNING (WorkflowEngine)
    ├── worker.execute(TaskDispatch) → TaskOutcome
    ├── COMPLETED/FAILED → RECORDED (WorkflowEngine)
    └── sync project state (StateEngine via WORKFLOW_RULE / TASK_OUTCOME)
```

### Execution lifecycle

| Phase | Task status | Worker status |
|-------|-------------|---------------|
| Eligible | `ready` | `available` |
| Assigned | `dispatched` | `assigned` |
| Executing | `running` | `executing` |
| Success | `completed` → `recorded` | `available` |
| Failure | `failed` | `available` |

### Capability matching

- Tasks declare `capability` in `*.workflow.toml` (maps to `WorkerCapability.work_type`).
- `matcher.select_worker()` finds executable workers via `WorkerRegistry.find_executable_by_capability()`.
- `mock.success` is preferred for normal workflow capabilities (`planning`, `validation`, `review`).
- `mock.failure` is selected only when task capability is `failure`.

### Mock workers

| Worker | ID | Capabilities | Behavior |
|--------|-----|--------------|----------|
| Echo | `mock.echo` | `echo` | Returns task name in outcome |
| Sleep | `mock.sleep` | `sleep` | Sleeps 50ms, succeeds |
| Success | `mock.success` | `planning`, `validation`, `review`, `success` | Always succeeds |
| Failure | `mock.failure` | `failure` | Always fails |

Mock workers are registered programmatically at bootstrap (`register_mock_workers`) and replace manifest-only placeholders with executable implementations.

### Runtime integration

`bootstrap()` now:
1. Discovers manifest workers
2. Registers mock executable workers
3. Creates `WorkerDispatcher` when a project with workflow engine is detected
4. Attaches dispatcher to `RuntimeContext`

### Project state sync

- Task starts running → `executing`
- Task outcome recorded → `task_outcome` trigger on failures/approvals
- Workflow progress reconciled → `workflow_rule` trigger

---

## 3. Public APIs

### Package: `vedaws.dispatch`

```python
from vedaws.dispatch import (
    WorkerDispatcher,
    run_until_idle,
    DispatchResult,
    DispatchStatus,
    RunSummary,
    match_workers,
    select_worker,
)
```

### `WorkerDispatcher`

| Method | Description |
|--------|-------------|
| `dispatch_and_execute(workflow_id, task_id, worker_id=None)` | Full dispatch lifecycle |
| `find_worker_for_task(task_def, preferred_worker_id=None)` | Capability match |
| `list_ready_tasks()` | Ready tasks from workflow engine |

### `vedaws.workers.execution`

```python
from vedaws.workers.execution import TaskDispatch, TaskOutcome, TaskOutcomeStatus
from vedaws.workers.interface import ExecutableWorker
```

### `WorkflowEngine` (extended)

| Method | Description |
|--------|-------------|
| `mark_dispatched(workflow_id, task_id, worker_id)` | READY → DISPATCHED |
| `mark_running(workflow_id, task_id)` | DISPATCHED → RUNNING |
| `record_worker_outcome(workflow_id, task_id, success, message)` | RUNNING → outcome |
| `ensure_executing(reason)` | Project state → executing |
| `sync_project_state(reason)` | Reconcile state from progress |

### `RuntimeContext` (extended)

```python
context.dispatcher  # WorkerDispatcher | None
```

### CLI

```bash
vedaws run [-C path]                 # Execute all ready tasks until idle
vedaws workers                       # List workers (shows EXEC column)
vedaws workers run <worker_id> [-C path] [workflow.task]
```

### Doctor checks (new)

- **dispatcher** — initialized with executable workers
- **execution pipeline** — all workflow task capabilities have compatible workers

---

## 4. Directory Structure

```
runtime/vedaws/dispatch/
├── __init__.py          # Public exports
├── dispatcher.py        # WorkerDispatcher — core orchestration
├── matcher.py           # Capability matching and worker selection
├── runner.py            # run_until_idle execution loop
├── models.py            # DispatchResult, RunSummary, DispatchStatus
└── reporter.py          # CLI output formatting

runtime/vedaws/workers/mock/
├── __init__.py
├── base.py              # MockWorker base class
├── metadata.py          # Shared metadata builder
├── registry.py          # create_mock_workers, register_mock_workers
├── echo.py              # EchoWorker
├── sleep.py             # SleepWorker
├── success.py           # SuccessWorker (default workflow)
└── failure.py           # FailureWorker (failure path testing)
```

---

## Tests

**46 tests passing** (8 new dispatch tests + 2 CLI tests + bootstrap assertion).

### Quick validation

```bash
vedaws init .
vedaws state transition initialized
vedaws workflow activate default
vedaws run
vedaws status
```

Expected: all three default workflow tasks complete via `mock.success`, workflow status `completed`.

---

## Non-goals (deferred)

| Area | Status |
|------|--------|
| Gemini, ChatGPT, Claude, Cursor | Not implemented |
| MCP, Unity | Not implemented |
| Real AI providers | Sprint 6+ |

---

## Next steps

- Replace mock workers with real provider adapters behind `ExecutableWorker`
- Add dispatch concurrency and worker availability pools
- Record execution history / audit log for dispatched tasks
