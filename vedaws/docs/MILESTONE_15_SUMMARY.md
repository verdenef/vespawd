# Milestone 15 Summary — Orchestration Hardening

**Status:** Complete  
**Version:** 0.1.0  
**Type:** Synchronous orchestration reliability hardening

Milestone 15 strengthens orchestration reliability and diagnostics without redesigning the runtime: deterministic run-loop behavior, bounded orchestration retries, explicit cancellation support, richer dispatch diagnostics, and read-only project detection during bootstrap.

---

## 1. Repository Tree

```
vedaws/
├── design/
│   ├── README.md
│   ├── 003_RUNTIME.md
│   ├── 007_PROJECT_MODEL.md
│   ├── 015_ROADMAP.md
│   └── 016_IMPLEMENTATION_PLAN.md
│
├── docs/
│   ├── API_STABILITY.md
│   └── MILESTONE_15_SUMMARY.md
│
├── runtime/vedaws/
│   ├── dispatch/
│   │   ├── models.py               # RunSummary diagnostics fields
│   │   ├── runner.py               # deterministic cycles + bounded retries + cancellation
│   │   └── reporter.py             # surfaced orchestration diagnostics
│   ├── project/detector.py         # detect_project(..., read_only=True|False)
│   └── runtime/bootstrap.py        # read-only detection during bootstrap
│
└── tests/
    ├── test_dispatch.py
    └── test_bootstrap.py
```

---

## 2. Architecture Summary

```
WorkflowEngine + WorkerDispatcher
        ↓
run_until_idle() deterministic cycle processing
        ↓
bounded retry across unresolved ready tasks
        ↓
explicit blocked/cancelled outcomes + diagnostics
        ↓
CLI/doctor-friendly orchestration visibility
```

Project detection now uses read-only mode during bootstrap so runtime context loading does not mutate `project.toml`.

---

## 3. Runtime Changes

| Area | Change |
|------|--------|
| Dispatch run loop | Reworked to process ready tasks deterministically per cycle |
| Retry behavior | Added bounded retry semantics for unresolved no-worker tasks across cycles |
| Cancellation | Added optional cancellation callback in `run_until_idle()` |
| Diagnostics | Added run-loop fields: `cycles`, `retries`, `blocking_reason`, `blocked_tasks`, `cancelled` |
| Reporting | Dispatch reporter now surfaces cycle/retry/blocking details |
| Project detection | Added `read_only` mode to `detect_project()` and used it in bootstrap |

Synchronous execution remains intact; no async queue, background workers, or job service were introduced.

---

## 4. Public API Changes

All changes are additive and backward-compatible.

| Surface | Change |
|---------|--------|
| `run_until_idle()` | Added optional args `max_cycles` and `stop_requested` |
| `RunSummary` | Added additive diagnostics fields (`cancelled`, `cycles`, `retries`, `blocking_reason`, `blocked_tasks`) |
| `detect_project()` | Added optional keyword arg `read_only` |

No breaking changes to:

- `WorkerDispatcher.dispatch_and_execute(...)`
- Capability-based worker matching
- `TaskDispatch` / `TaskOutcome` execution contract
- Automation action model (`execute_worker` remains orchestration boundary)

---

## 5. Design Decisions

1. **Keep orchestration synchronous:** harden current model instead of introducing async/job redesign in M15.
2. **Deterministic run loop:** process ready tasks in stable sorted order each cycle for debuggability.
3. **Retry only where safe:** retries apply to unresolved orchestration readiness (e.g. no compatible worker), not to opaque worker side-effect execution.
4. **Explicit blocking diagnostics:** when orchestration halts, reason/task context is captured and reported.
5. **Read-only detection by default in bootstrap:** remove write-on-read behavior from runtime startup path.

---

## 6. Test Coverage

| Test file | Coverage |
|-----------|----------|
| `tests/test_dispatch.py` | no-worker retry/block behavior and cancellation behavior |
| `tests/test_bootstrap.py` | bootstrap uses read-only detection and does not mutate `project.toml` |

All existing dispatch/state/plugin/automation/AI tests continue to pass.

---

## 7. Deferred Work

- Async dispatch queues and persistent job status model
- Distributed orchestration and remote worker execution
- Scheduling/background automation
- Structured event payload schema versioning
- Advanced retry policies for side-effecting workers (requires stronger idempotency contracts)

---

## 8. Test Results

```bash
python -m pytest tests/ -q
# 118 passed in 9.80s
```
