# Executor Phase 5 Audit

**Date:** 2026-07-02  
**Scope:** Executor Spec §6 (design gate) and §8.2 (`pre_implement_check`); Bridge public CLI only  
**Package:** `main/executor/lib/vespawd_executor/orchestration/gate.py`, `orchestration/types.py` (`GateResult`)  
**Tests:** 82/82 passing (`python -m pytest -q` in `main/executor/`)

---

## Requirements traceability

| Spec ref | Requirement | Implementation | Test | Status |
|----------|-------------|----------------|------|--------|
| §8.2 | Invoke `pre_implement_check` before implementation | `run_pre_implement_check()` → `BridgeClient.invoke("pre_implement_check", ...)` | `test_gate_allows_when_ok`, live | Pass |
| §8.2 | Validate design gate | interpret `design_gate_blocked` / `design_gate_overridden` codes | `test_gate_blocks_on_design_gate`, `test_gate_design_override_allows` | Pass |
| §8.2 | Validate doctor non-blocking | interpret `doctor_blocked`; surface `doctor_summary` | `test_gate_doctor_blocked` | Pass |
| §8.2 | Project state allows executing | interpret `state_ineligible` | `test_gate_blocks_on_workflow_ineligible` | Pass |
| §8.2 | Workflow task matches parsed phase | interpret `workflow_task_mismatch` (warning) | `test_gate_task_mismatch_is_warning` | Pass |
| §8.2 | On failure: do not edit `main/src/` | `allow_implement = not should_block_implement(check)` | all `test_gate_blocks_on_*` | Pass |
| §6.1–6.2 | Design gate controls execution | `design_gate_blocked`/`overridden` flags on `GateResult` | design gate tests | Pass |
| §8, §14 | Bridge via public CLI only | `BridgeClient` subprocess; no `vespawd_bridge` import | all gate tests | Pass |
| §11.5 | Recovery guidance from Bridge | `extract_recovery_actions()` | `test_gate_blocks_on_design_gate` | Pass |
| — | Bridge invocation failure blocks | `EXECUTOR_BRIDGE_FAILURE_CODES` → block | `test_gate_blocks_on_bridge_failure` | Pass |
| — | Idempotent repeated checks (read-only) | no state mutation in gate | `test_gate_idempotent_repeated`, `test_live_gate_idempotent` | Pass |

---

## Bridge invocation validation

| Aspect | Behavior |
|--------|----------|
| Operation | `pre_implement_check` (single public op, per requirement) |
| Payload | `{ current_task, skip_design, design_later }` from `ExecutorContext.session` |
| Validation logic | Owned entirely by Bridge (`validate_design_gate`, `validate_doctor`, `validate_workflow_eligibility`, `validate_task_alignment`); Executor never duplicates |
| Decision source | `BridgeResult.codes` → `should_block_implement()` blocking-code guard |
| Boundary | Executor reads `BridgeResultView` only; no direct Bridge internals |

### Code classification consumed by the gate

| Code | Class | Gate effect |
|------|-------|-------------|
| `design_gate_blocked` | blocking | `allow_implement=False`, `design_gate_blocked=True` |
| `state_ineligible` | blocking | `allow_implement=False`, `workflow_ineligible=True` |
| `doctor_blocked` | blocking | `allow_implement=False`, `doctor_blocked=True` |
| `bridge_missing` / `bridge_invoke_failed` / `cli_*` | blocking | `allow_implement=False` |
| `design_gate_overridden` | warning | allowed; `design_gate_overridden=True` |
| `workflow_task_mismatch` | warning | allowed; `task_mismatch=True` |

---

## Public API

| Symbol | Purpose |
|--------|---------|
| `run_pre_implement_check(paths, ctx, current_task)` | §8.2 gate; returns `GateResult` |
| `GateResult` | `allow_implement`, `design_gate_blocked`, `design_gate_overridden`, `workflow_ineligible`, `task_mismatch`, `doctor_blocked`, `blockers`, `warnings`, `recovery`, `check`, `to_dict()` |

---

## Deferred to later phases

| Spec ref | Requirement | Phase |
|----------|-------------|-------|
| §7 / §8.3 | Userspace implementation + `post_implement` | Phase 6 |
| §6.3 | DESIGN.md screen-by-screen enforcement in code | Phase 6 (UI implementation) |
| §11.5 | Append gate blockers to `current_task.md` Notes | Phase 6/8 |
| §8.4–8.5 | Complete + documenter hooks | Phase 7 |

---

## Documented ambiguities (not invented)

| ID | Topic | Phase 5 handling |
|----|-------|------------------|
| A-13 | Task-mismatch severity | Bridge emits `workflow_task_mismatch` as warning (non-blocking); gate mirrors — implement proceeds with warning surfaced |
| A-14 | Offline Bridge during gate | `pre_implement_check` requires live Vedaws (doctor/state/workflow). Unlike `sync_status`, no offline exemption defined; gate treats invocation failure as blocking. No `orchestration_offline` allow-path added (would bypass validation) |
| A-15 | Gate persistence | §8.2 is a validation check; spec does not require writing gate results to PAWS. Gate is pure read → idempotent by construction |

---

## Gaps / notes

| Item | Classification | Note |
|------|----------------|------|
| Gate does not write PAWS | Intentional | §8.2 is read-only validation; recording blockers to `current_task.md` deferred (A-15/§11.5) |
| No new CLI subcommand | Intentional | Consistent with Phase 4 (orchestration is library-level; CLI exposes `startup` only) |
| Bridge not modified | Constraint | Met |
| No direct `vespawd_bridge` import | Intentional | Subprocess CLI only |
| Design-block integration test tolerant | Intentional | `test_live_gate_design_block_for_ui` asserts consistency (blocked ⇒ flag/blocker set) without over-constraining Bridge doctor/state prerequisites |

---

## Phase 5 verdict

**PASS** — `pre_implement_check` is invoked solely through the public Bridge CLI, all validation remains Bridge-owned, and the Executor correctly gates userspace implementation on blocking codes while surfacing design-gate, workflow-eligibility, task-mismatch, doctor, and recovery guidance. Idempotent by construction (read-only). All 82 tests pass.

---

*Stop here per phased implementation plan. Do not begin Phase 6 until approved.*
