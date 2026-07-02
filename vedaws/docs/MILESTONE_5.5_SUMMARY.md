# Milestone 5.5 Summary — Architecture Cleanup

**Status:** Complete  
**Version:** 0.1.0  
**Type:** Refactoring and stabilization (no new features)

Milestone 5.5 strengthens the existing Vedaws architecture ahead of the Plugin SDK milestone. Work focused on design–implementation alignment, shared state-transition logic, dispatch eligibility, public API clarity, and documentation.

---

## 1. Repository Tree

```
vedaws/
├── design/
│   ├── README.md                 # Updated layer diagram
│   ├── 002_CORE.md               # Project lifecycle → 006 alignment
│   ├── 006_STATE_MACHINE.md      # Dispatch eligibility + v0.2.1
│   ├── 007_PROJECT_MODEL.md      # NEW content — .vedaws layout
│   ├── 010_PLUGINS.md            # NEW content — discovery-only status
│   └── 012_CONFIGURATION.md      # NEW content — config schema
│
├── docs/
│   ├── ARCHITECTURE_AUDIT_MILESTONE_5.md
│   └── MILESTONE_5.5_SUMMARY.md
│
├── runtime/vedaws/
│   ├── project/state/
│   │   ├── bridge.py             # NEW — shared transition + bridges
│   │   └── eligibility.py        # NEW — orchestration/dispatch rules
│   ├── workflow/engine.py        # Uses bridge; state_engine property
│   ├── dispatch/
│   │   ├── dispatcher.py         # Dispatch eligibility checks
│   │   └── matcher.py            # Deterministic worker selection
│   ├── workers/
│   │   ├── manifest_worker.py    # Clearer manifest-only messaging
│   │   └── reporter.py           # runtime vs manifest column
│   └── runtime/bootstrap.py      # Documented mock override
│
└── tests/
    ├── test_state_cleanup.py     # NEW — bridge, eligibility, sync
    └── (52 tests total, all passing)
```

---

## 2. Architecture Summary

The implemented stack (unchanged in shape, strengthened in consistency):

```
CLI → RuntimeContext → WorkerDispatcher → WorkflowEngine (+ TaskRegistry) → StateEngine
                              ↓
                       WorkerRegistry (ExecutableWorker | ManifestWorker)
                              ↓
                       PluginRegistry (manifest discovery only)
```

**Key stabilization principles applied:**

- **Single transition path** — `apply_state_transition()` in `project/state/bridge.py` used by workflow sync and explicit transitions (includes bridge support).
- **Explicit eligibility** — `allows_orchestration`, `allows_dispatch`, and `dispatch_blocked_reason` in `project/state/eligibility.py`.
- **Dispatch gates** — `WorkerDispatcher` checks project state; promotes to `executing` when allowed; skips with clear message otherwise.
- **Deterministic worker selection** — first compatible worker by sorted `id` (removed hardcoded `mock.success` preference).
- **Design authority** — `006_STATE_MACHINE.md` remains canonical for operational states; `002_CORE.md` maps conceptual phases to it.

---

## 3. Refactors Performed

| Area | Change |
|------|--------|
| **State transitions** | Extracted `bridge.py` with `transition_bridge()` and `apply_state_transition()` |
| **WorkflowEngine** | `_sync_project_state` and `_try_state_transition` delegate to shared helper |
| **WorkflowEngine** | Added `state_engine` property; `WORKFLOWS_DIR` uses `config.paths` constant |
| **Dispatcher** | Eligibility check + `ensure_executing` before dispatch |
| **Matcher** | Removed `mock.success` hardcoding; deterministic `worker.id` sort |
| **ManifestWorker** | Updated docstrings and health message (`manifest-only`) |
| **Workers reporter** | `EXEC` column shows `runtime` vs `manifest` |
| **Bootstrap** | Comment on mock worker override behavior |
| **ProjectState** | `allows_orchestration` / `allows_dispatch` delegate to eligibility module |
| **Public API** | Exported bridge and eligibility symbols from `vedaws.project.state` |

**Not changed (intentionally):**

- No Plugin SDK, event bus, automation, AI providers
- `vedaws tasks complete/fail` retained for testing (documented as bypass)
- No file moves between packages
- No breaking CLI changes

---

## 4. Design Documents Updated

| Document | Update |
|----------|--------|
| `design/README.md` | Implemented layer diagram; status bumps for 002, 007, 010, 012 |
| `design/002_CORE.md` | v0.1.1 — lifecycle references `006`; conceptual mapping table |
| `design/006_STATE_MACHINE.md` | v0.2.1 — dispatch promotion footnote; planning dispatch clarified |
| `design/007_PROJECT_MODEL.md` | Full `.vedaws/` structure and `ProjectContext` |
| `design/010_PLUGINS.md` | Current discovery model + Milestone 6 boundaries |
| `design/012_CONFIGURATION.md` | Implemented config schema and env vars |

---

## 5. Technical Debt Remaining

| Item | Priority | Notes |
|------|----------|-------|
| Dispatch audit log (`dispatches.jsonl`) | High | Required by `003_RUNTIME.md`; deferred to Milestone 6+ |
| `tasks complete/fail` worker bypass | Medium | Documented; consider dev-only flag later |
| Approval gate enforcement | Medium | `requires_approval` records state after outcome, does not block dispatch |
| Plugin activation & contributions | High | Milestone 6 scope |
| Manifest worker executor binding | High | `executor` field not yet in manifest schema |
| Capability `scope` matching | Medium | Tasks use string only; workers have scope dimension |
| Empty design stubs (005, 008–009, 011, 013–016) | Medium | Still TODO-only |
| Async execution substrate | Medium | Required before real AI providers |
| `paused` project semantics | Low | Mapped to `blocked` in 002 until designed |
| Proprietary license | High for OSS | Not addressed in this milestone |
| `StateEngine.subscribe()` unused | Low | Event bus deferred |

---

## 6. Readiness Assessment for Milestone 6 (Plugin SDK)

| Criterion | Status | Notes |
|-----------|--------|-------|
| Stable core package boundaries | ✅ Good | `project/`, `workflow/`, `dispatch/`, `workers/` clear |
| Design docs for project & config | ✅ Good | 007, 012 authored |
| Plugin doc baseline | ✅ Good | 010 defines current vs target |
| State/workflow/dispatch alignment | ✅ Improved | Eligibility enforced |
| Public extension points | ⚠️ Partial | Manifest discovery only; no loader protocol |
| Worker executor binding | ❌ Missing | Need manifest `executor` or entry point |
| Per-project plugin activation | ❌ Missing | `.vedaws/plugins.toml` or equivalent |
| Dispatch auditability | ❌ Missing | Should accompany SDK for traceability |
| Test coverage | ✅ Adequate | 52 tests; bridge and eligibility covered |

**Verdict:** **Ready to begin Milestone 6 planning** with clear prerequisites:

1. Extend `010_PLUGINS.md` with activation file format and contribution protocol  
2. Define worker `executor` binding in manifests (`004_WORKERS.md` + implementation)  
3. Implement per-project plugin activation in `.vedaws/`  
4. Keep using `apply_state_transition` and eligibility modules for new hooks  

**Estimated SDK readiness:** ~40% infrastructure, ~15% plugin-specific (up from audit's ~15% / ~15%).

---

## Tests

```bash
python -m pytest tests/ -q
# 52 passed
```

New: `tests/test_state_cleanup.py` (6 tests) for bridges, eligibility, and sync behavior.

---

## Non-goals (confirmed)

Plugin SDK, Event Bus, Automation Engine, AI Providers, Unity, Git, MCP — **not implemented**.
