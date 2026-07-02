# Executor Implementation Checklist

**Spec:** [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md)  
**Bridge dependency:** `main/bridge/` (stable; invoke via CLI only)  
**Package:** `main/executor/lib/vespawd_executor/`

---

## Phases

| Phase | Scope (Executor Spec) | Status |
|-------|----------------------|--------|
| **1** | §3 Startup — discovery, validation, bridge bootstrap + sync | **Complete** |
| **2** | §4 Master Prompt parsing | **Complete** |
| **3** | §5 PAWS synchronization (context, task, backlog writers) | **Complete** |
| **4** | §5.3–5.4 + §8 Bridge ingest / sync orchestration | **Complete** |
| **5** | §6 Design gate + §8.2 `pre_implement_check` | **Complete** |
| **6** | §7 Userspace implementation policy + §8.3 `post_implement` | **Complete** |
| **7** | §8.4–8.5 Complete + documenter hooks; §13 HANDOFF | **Complete** |
| **8** | §10–12 Completion, recovery, reporting; §14 tool neutrality | **Complete** |

Each phase: implement → test → audit → **stop and wait** before next phase.

---

## Phase 1 — Startup (§3)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P1-01 | Workspace root discovery | `paths/resolver.py` | `test_paths.py` |
| P1-02 | Resolve POS, userspace, Vedaws roots (§3.5) | `paths/resolver.py` | `test_paths.py` |
| P1-03 | Master Prompt trigger recognition (§3.1) | `startup/trigger.py` | `test_trigger.py` |
| P1-04 | Startup validation (§3.4) | `startup/validate.py` | `test_validate.py` |
| P1-05 | Bridge client via subprocess CLI (§8, §14) | `bridge/client.py` | `test_bridge_client.py` |
| P1-06 | Startup sequence: bootstrap + sync_status (§3.6–3.7) | `startup/sequence.py` | `test_startup.py` |
| P1-07 | Interpret `BridgeResult` blockers/warnings | `bridge/interpret.py` | `test_startup.py` |

---

## Ambiguities (document, do not invent)

| ID | Topic | Notes |
|----|-------|-------|
| A-01 | Bootstrap timing vs parse | §3.6 startup bootstrap vs §8.1 "before parse writes" vs §5.3 "write PAWS then ingest" — Phase 1 follows §3.6; ingest deferred to Phase 4 |
| A-02 | §8.1 bootstrap "before parse writes" | Conflicts with §5.3 ordering; Executor will bootstrap at startup if `.vedaws/` missing, re-sync after PAWS writes in Phase 4 |
| A-03 | Backlog in bridge manifest (§4.5) | Bridge does not implement; Executor owns `backlog.md` only |

---

## Phase 2 — Master Prompt parsing (§4)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P2-01 | H1 + H2 section structure (§4.1) | `parse/sections.py` | `test_sections.py` |
| P2-02 | Legacy `# CURSOR MASTER PROMPT` H1 | `parse/sections.py` | `test_sections.py`, `legacy fixture` |
| P2-03 | Legacy `CURSOR INSTRUCTIONS` alias | `parse/sections.py` | `test_instructions.py` |
| P2-04 | PROJECT BRIEF extraction (§4.2) | `parse/engine.py` | `test_parse_engine.py` |
| P2-05 | PROJECT CONTEXT UPDATES parse (§4.3) | `parse/context_updates.py` | `test_context_updates.py` |
| P2-06 | CURRENT TASK Goal/Status/Criteria (§4.4) | `parse/current_task.py` | `test_current_task.py` |
| P2-07 | BACKLOG ITEMS parse (§4.5) | `parse/backlog.py` | `test_backlog.py` |
| P2-08 | EXECUTOR INSTRUCTIONS parse (§4.6) | `parse/instructions.py` | `test_instructions.py` |
| P2-09 | Parse failure §4.7 | `parse/engine.py` | `test_parse_engine.py` |
| P2-10 | Phase hint for Bridge ingest | `parse/phase_hint.py` | `test_phase_hint.py` |
| P2-11 | `to_ingest_payload()` shape (Phase 4 prep) | `parse/engine.py` | `test_parse_engine.py` |

---

## Phase 3 — PAWS synchronization (§5)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P3-01 | Merge `project_context.md` (§4.3, §5.2) | `sync/project_context.py` | `test_sync_project_context.py` |
| P3-02 | Write `current_task.md` (§4.4) | `sync/current_task.py` | `test_sync_current_task.py` |
| P3-03 | Append `backlog.md` skip duplicates (§4.5) | `sync/backlog.py` | `test_sync_backlog.py` |
| P3-04 | Seed HANDOFF on ingest (§5.3 step 4, §13.1) | `sync/handoff.py` | `test_sync_handoff.py` |
| P3-05 | Orchestrate PAWS writes (no Bridge) | `sync/engine.py` | `test_sync_paws.py` |
| P3-06 | Atomic writes | `sync/io.py` | via integration tests |
| P3-07 | Idempotent re-sync | all writers | `test_sync_paws.py`, unit idempotent tests |

---

## Phase 4 — Bridge orchestration (§5.3, §5.4, §8)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P4-01 | §5.3 step 1 PAWS scheduler before Bridge | `sync/engine.py` `sync_paws_scheduler()` | `test_orchestration_ingest.py` |
| P4-02 | §5.3 step 2 `ingest_master_prompt` via CLI | `orchestration/ingest.py` | `test_orchestration_ingest.py` |
| P4-03 | §5.3 step 3 `sync_status` after ingest | `orchestration/ingest.py` | `test_orchestration_ingest.py` |
| P4-04 | §5.3 step 4 HANDOFF after Bridge | `seed_handoff_from_parse()` | `test_orchestration_ingest.py` |
| P4-05 | §5.4 `post_phase_complete` + `sync_status` | `orchestration/complete.py` | `test_orchestration_complete.py` |
| P4-06 | BridgeResult blockers/warnings/recovery | `bridge/interpret.py` | `test_bridge_interpret.py` |
| P4-07 | Offline sync_status handling | `bridge/interpret.py` | `test_offline_sync_after_ingest` |
| P4-08 | Ingest failure still runs sync (§11.5) | `orchestration/ingest.py` | `test_ingest_failure_still_syncs` |
| P4-09 | Live integration ingest + complete | `test_orchestration.py` | integration |

---

## Phase 5 — Pre-implementation gate (§6, §8.2)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P5-01 | Invoke public `pre_implement_check` via CLI | `orchestration/gate.py` | `test_gate.py` |
| P5-02 | Build payload (current_task, skip_design, design_later) | `orchestration/gate.py` | `test_gate_design_override_allows` |
| P5-03 | Prevent implement on blocking codes (§8.2) | `orchestration/gate.py` | `test_gate_blocks_on_*` |
| P5-04 | Design gate decision surfaced (§6.1–6.2) | `orchestration/gate.py` | `test_gate_blocks_on_design_gate`, `test_gate_design_override_allows` |
| P5-05 | Workflow eligibility / state_ineligible | `orchestration/gate.py` | `test_gate_blocks_on_workflow_ineligible` |
| P5-06 | Task mismatch as warning (non-blocking) | `orchestration/gate.py` | `test_gate_task_mismatch_is_warning` |
| P5-07 | Doctor blocked surfaced | `orchestration/gate.py` | `test_gate_doctor_blocked` |
| P5-08 | Bridge failure blocks implement | `orchestration/gate.py` | `test_gate_blocks_on_bridge_failure` |
| P5-09 | Recovery guidance extracted | `orchestration/gate.py` | `test_gate_blocks_on_design_gate` |
| P5-10 | Idempotent repeated checks | `orchestration/gate.py` | `test_gate_idempotent_repeated`, `test_live_gate_idempotent` |
| P5-11 | Live gate after ingest | `orchestration/gate.py` | `test_gate_live.py` (integration) |

---

## Phase 6 — Userspace policy + post_implement (§7, §8.3)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P6-01 | Allowed directories (§7.1) | `policy/userspace.py` | `test_userspace_policy.py` |
| P6-02 | Forbidden directories (§7.2) | `policy/userspace.py` | `test_userspace_policy.py` |
| P6-03 | `project_context.md` writable but kernel `.ai` forbidden | `policy/userspace.py` | `test_project_context_allowed_but_kernel_forbidden` |
| P6-04 | Layout-aware (`paws022/src` forbidden in sidecar) | `policy/userspace.py` | `test_wrong_userspace_forbidden_in_sidecar` |
| P6-05 | Aggregate report (allowed/forbidden/unknown) | `policy/userspace.py` | `test_check_changed_paths_aggregates` |
| P6-06 | §8.3 Progress Log files-changed summary | `sync/progress_log.py` | `test_progress_log.py` |
| P6-07 | Progress Log idempotent (no duplicate row) | `sync/progress_log.py` | `test_idempotent_same_row` |
| P6-08 | §8.3 `bridge.post_implement` via CLI | `orchestration/implement.py` | `test_success_records_and_hooks` |
| P6-09 | `sync_status` after post_implement (§8.1) | `orchestration/implement.py` | `test_success_records_and_hooks` |
| P6-10 | Forbidden edit blocks before hooks | `orchestration/implement.py` | `test_forbidden_edit_blocks_before_hooks` |
| P6-11 | Non-strict worker failure = warning (ok-authoritative) | `orchestration/implement.py` | `test_nonstrict_worker_failure_is_warning` |
| P6-12 | Strict/Bridge failure blocks | `orchestration/implement.py` | `test_strict_failure_blocks`, `test_bridge_missing_blocks` |
| P6-13 | Offline sync does not block | `orchestration/implement.py` | `test_offline_sync_does_not_block` |
| P6-14 | Idempotent repeated post_implement | `orchestration/implement.py` | `test_idempotent_repeated`, live |
| P6-15 | Live post_implement after ingest | `orchestration/implement.py` | `test_post_implement_live.py` (integration) |

---

## Phase 7 — Completion + documenter hooks (§5.4, §8.4–8.5, §10.6, §13)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P7-01 | §5.4 step 2 `post_phase_complete` via CLI | `orchestration/finalize.py` (reuses `complete.py`) | `test_completion.py` |
| P7-02 | §5.4 step 3 `sync_status` after complete | `orchestration/complete.py` | `test_completion.py` |
| P7-03 | §5.4 step 4 HANDOFF full refresh (§13) | `sync/handoff.py` `refresh_handoff()` | `test_handoff_refresh.py` |
| P7-04 | §13.2 required sections (facts-only, fill empty) | `sync/handoff.py` | `test_refresh_fills_empty_sections` |
| P7-05 | §13.3 facts from task/context | `handoff_facts_from_task()` | `test_facts_from_task_splits_checkboxes` |
| P7-06 | §5.4 step 5 / §10.6 `tasks/completed/` log | `sync/completed.py` | `test_completed_log.py` |
| P7-07 | §10.6 `current_task.md` Status idle | `sync/current_task.py` `set_task_status()` | `test_task_status.py` |
| P7-08 | §10.6 Progress Log close-out entry | `orchestration/finalize.py` | `test_completion_full_sequence` |
| P7-09 | Close-out only when outcome=completed + Bridge ok | `orchestration/finalize.py` | `test_completion_stops_when_bridge_denies`, `test_completion_non_completed_outcome_skips_closeout` |
| P7-10 | §8.5 `pre_documenter` via CLI | `orchestration/documenter.py` | `test_pre_documenter.py` |
| P7-11 | §13.5 handoff-ready signal | `DocumenterResult.handoff_ready` | `test_documenter_ready`, `test_documenter_stale_handoff_warns` |
| P7-12 | Artifacts/doctor blocking surfaced | `orchestration/documenter.py` | `test_documenter_artifacts_missing_blocks`, `test_documenter_doctor_blocked` |
| P7-13 | Idempotent HANDOFF refresh + completed log | all writers | `test_refresh_idempotent`, `test_completion_idempotent`, live |
| P7-14 | Live completion + documenter | integration | `test_completion_live.py` |

---

## Phase 8 — Reporting, recovery, tool neutrality (§10.7, §11.5, §12, §14)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| P8-01 | §10.7 report: what changed | `reporting/report.py` | `test_report.py` |
| P8-02 | §10.7 report: how to run/test | `reporting/report.py` | `test_report_includes_required_sections` |
| P8-03 | §10.7 report: HANDOFF current | `reporting/report.py` | `test_report_includes_required_sections` |
| P8-04 | §10.7 report: next suggested action | `NextAction` inference | `test_*_action` |
| P8-05 | §13.5 handoff-ready signal in report | `reporting/report.py` | `test_handoff_ready_signal_and_planner_action` |
| P8-06 | §11.5 record orchestration error in Notes | `sync/notes.py` | `test_task_notes.py` |
| P8-07 | §12.5 debugging notes (custom prefix) | `sync/notes.py` | `test_custom_prefix` |
| P8-08 | Notes idempotent (no duplicate bullet) | `sync/notes.py` | `test_idempotent_same_note` |
| P8-09 | §12.3 resume: read current_task/status/context | `recovery/resume.py` | `test_resume.py` |
| P8-10 | §12.3 resumable when active task + goal | `recovery/resume.py` | `test_resumable_in_progress`, `test_not_resumable_idle` |
| P8-11 | §12.3 missing-artifact warnings | `recovery/resume.py` | `test_missing_*` |
| P8-12 | §14 no Bridge-internal / vendor imports | `test_tool_neutrality.py` | `test_no_forbidden_imports_anywhere` |
| P8-13 | §14 Bridge via subprocess only | `test_tool_neutrality.py` | `test_bridge_only_via_subprocess` |
| P8-14 | §14 report terminology neutral | `reporting/report.py` | `test_report_has_no_vendor_terminology` |
| P8-15 | Deterministic report + resume | `reporting/`, `recovery/` | `test_report_deterministic`, `test_deterministic` |

---

*Updated as phases complete. All Executor phases (1–8) complete.*
