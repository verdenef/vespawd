# Vespawd Bridge — Implementation Checklist & Execution Plan

**Status:** Planning artifact (pre-implementation)  
**Source of truth:** [BRIDGE_IMPLEMENTATION_SPEC.md](BRIDGE_IMPLEMENTATION_SPEC.md)  
**Secondary references:** [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md), [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md)  
**Constraint:** MUST NOT modify `paws022/` or `vedaws/`

---

## Execution plan (module order)

| Phase | Module | Deliverables | Gate (all MUSTs for phase verified) |
|-------|--------|--------------|-------------------------------------|
| **0** | Planning | This checklist | — |
| **1** | Directory structure | §2 tree, `manifest.toml`, `spec/VERSION`, templates | §2, §5.1 paths |
| **2** | Manifest system | loader, schema validation, `ManifestModel` | §1.5, §5 |
| **3** | Public API | types, `invoke()`, input models | §1.3, §3.1, §3.4 |
| **4** | Path resolver | `ResolvedPaths`, layout, project_context | §3.2, §5.2, §8.4 |
| **5** | Logging | correlation, events, levels | §10 |
| **6** | CLI adapter | allowlist, subprocess, retry, timeout | §1.6, §6, Bridge Spec §7.1 |
| **7** | Validation engine | all validators | §8 |
| **8** | Recovery engine | codes → hints, retry policy | §9.2, §9.3 |
| **9** | Projection engine | status.md, Notes, HANDOFF mirror | §7, Bridge Spec §6 |
| **10** | Dispatcher | prepare pipeline, handler registry | §1.4 |
| **11** | Operations (×7) | handlers per §4 | §4.1–4.7 |
| **12** | `bin/bridge` CLI | JSON invoke transport | §1.3, App C |
| **13** | Hooks (OPTIONAL) | README + no-op examples | §12.1 |
| **14** | Tests | unit, integration, recovery, idempotency, contract | §11 |
| **15** | README | Executor integration | §2.1, App A |
| **16** | Final audit | MUST compliance table | User requirement |

**Rule:** After each phase — implement tests for that phase before proceeding.

**Language choice (decision, conservative):** Python 3.11+ — matches Vedaws runtime; subprocess-friendly; no IDE coupling. Document in `main/bridge/README.md`.

---

## 1. Required modules

| ID | Module | Spec § | MUST requirements |
|----|--------|--------|-------------------|
| M-01 | Public API (`lib/api/`) | §1.3, §3 | Single entry `invoke()`; 7 operations; `BridgeContext` + `BridgeResult`; no inline operation logic |
| M-02 | Operation dispatcher (`lib/dispatcher/`) | §1.4 | 12-step prepare pipeline; abort on step 3–6 failure; no direct Vedaws spawn |
| M-03 | Manifest loader (`lib/manifest/`) | §1.5, §5 | Read `bridge/manifest.toml`; immutable `ManifestModel`; MUST NOT guess missing keys |
| M-04 | Path resolver (`lib/manifest/` or sub) | §3.2, §5.2 | `ResolvedPaths` all fields; layout sidecar/integrated; MUST NOT write PAWS except via projection |
| M-05 | CLI adapter (`lib/cli/`) | §1.6, §6 | Only module spawning subprocesses; allowlist; `--path` on every command |
| M-06 | Projection engine (`lib/projection/`) | §1.7, §7 | status.md atomic write; Notes enrichment; MUST NOT overwrite Goal/Criteria/backlog |
| M-07 | Validation engine (`lib/validation/`) | §1.8, §8 | Composable validators; `ValidationResult` |
| M-08 | Recovery engine (`lib/recovery/`) | §1.9, §9.2 | Map codes → `RecoveryHint`; CLI retry per §6.4; MUST NOT auto-destruct `.vedaws/` |
| M-09 | Logging (`lib/logging/`) | §10 | Correlation ID; required events; MUST NOT log secrets/HANDOFF prose |
| M-10 | Operation handlers (`lib/operations/*`) | §4 | One handler per operation; sequences exact |
| M-11 | CLI entry (`bin/bridge`) | §1.3 | `bridge invoke <op>` JSON I/O |
| M-12 | Hooks (`hooks/`) OPTIONAL | §12.1 | Stubs only v1; MUST NOT violate hook rules |

---

## 2. Required operations

| ID | Operation | Spec § | Key MUSTs |
|----|-----------|--------|-----------|
| OP-01 | `bootstrap` | §4.1 | Idempotent; doctor blocks ok; workflow active; init if no `.vedaws/` |
| OP-02 | `ingest_master_prompt` | §4.2 | Returns `vedaws_task_id`; MUST NOT run `vedaws run` on ingest; sync after |
| OP-03 | `sync_status` | §4.3 | Idempotent; offline projection if vedaws missing; atomic status.md |
| OP-04 | `pre_implement_check` | §4.4 | ok=true iff zero blocking codes; all §8 validators |
| OP-05 | `post_implement` | §4.5 | `cli.run` bounded; ok=true unless strict manifest mode |
| OP-06 | `post_phase_complete` | §4.6 | tasks complete; human_gate → awaiting_approval; chained sync |
| OP-07 | `pre_documenter` | §4.7 | artifacts_missing blocks; optional HANDOFF mirror |

---

## 3. Required interfaces

### 3.1 BridgeContext (§3.1)

| Field | Required | Checklist ID |
|-------|----------|--------------|
| `workspace_root` | YES | IF-01 |
| `correlation_id` | NO | IF-02 |
| `session_overrides` | NO | IF-03 |
| `session_overrides.skip_design` | NO | IF-03a |
| `session_overrides.design_later` | NO | IF-03b |
| `session_overrides.force_phase` | NO | IF-03c |
| `session_overrides.human_approved_destructive_recovery` | NO | IF-03d |
| `executor_metadata` | NO | IF-04 |

### 3.2 Operation inputs (§4, §3)

| Type | Fields | Checklist ID |
|------|--------|--------------|
| `BootstrapInput` | (minimal / name optional) | IF-10 |
| `MasterPromptIngest` | goal, acceptance_criteria required; constraints, notes, product_name, phase_hint optional | IF-11 |
| `SyncInput` | (paths from context) | IF-12 |
| `ImplementGateInput` | current_task required; skip_design, design_later optional | IF-13 |
| `PostImplementInput` | vedaws_task_id required; changed_paths optional | IF-14 |
| `PhaseCompleteInput` | vedaws_task_id, outcome required; reason, human_gate optional | IF-15 |
| `DocumenterGateInput` | (paths from context) | IF-16 |

### 3.3 ResolvedPaths (§3.2)

| Field | Checklist ID |
|-------|--------------|
| `pos_root` | IF-20 |
| `vedaws_project_root` | IF-21 |
| `userspace_root` | IF-22 |
| `manifest_path` | IF-23 |
| `current_task_path` | IF-24 |
| `status_path` | IF-25 |
| `handoff_path` | IF-26 |
| `design_gate_path` | IF-27 |
| `project_context_path` | IF-28 |
| `layout` | IF-29 |

### 3.4 VedawsSnapshot (§3.3)

| Field | Checklist ID |
|-------|--------------|
| `project_state` | IF-30 |
| `active_workflow_id` | IF-31 |
| `active_task_id` | IF-32 |
| `task_states` | IF-33 |
| `doctor_ok` | IF-34 |
| `doctor_summary` | IF-35 |
| `artifacts_report` | IF-36 |
| `raw_outputs` | IF-37 |

### 3.5 CliResult (§3.6)

| Field | Checklist ID |
|-------|--------------|
| `exit_code` | IF-40 |
| `stdout` | IF-41 |
| `stderr` | IF-42 |
| `timed_out` | IF-43 |

### 3.6 ValidationResult (§8)

| Field | Checklist ID |
|-------|--------------|
| `passed` | IF-50 |
| `codes` | IF-51 |
| `messages` | IF-52 |

---

## 4. BridgeResult fields (§3.4) — all MUST be present

| Field | Checklist ID |
|-------|--------------|
| `ok` | BR-01 |
| `operation` | BR-02 |
| `correlation_id` | BR-03 |
| `codes` | BR-04 |
| `blockers` | BR-05 |
| `warnings` | BR-06 |
| `vedaws_task_id` | BR-07 |
| `project_state` | BR-08 |
| `doctor_summary` | BR-09 |
| `files_touched` | BR-10 |
| `recovery` | BR-11 |
| `duration_ms` | BR-12 |
| `vedaws_commands_run` | BR-13 |

---

## 5. RecoveryHint fields (§9.2)

| Field | Checklist ID |
|-------|--------------|
| `code` | RH-01 |
| `action` | RH-02 |
| `retry_operation` | RH-03 |
| `destructive` | RH-04 |

---

## 6. Validators (§8)

| ID | Validator | Spec § | Used by |
|----|-----------|--------|---------|
| V-01 | `validation.layout` | §8.4 | dispatcher prepare, bootstrap, pre_implement |
| V-02 | `validation.version` | §8.5 | dispatcher prepare, bootstrap |
| V-03 | `validation.manifest_schema` | §5.2 | manifest loader |
| V-04 | `validation.manifest_integrity` | §4.4 | pre_implement |
| V-05 | `validation.doctor` (strict/soft) | §8.1 | pre_implement, pre_documenter, bootstrap |
| V-06 | `validation.design_gate` | §8.2 | pre_implement |
| V-07 | `validation.workflow_eligibility` | §8.3 | pre_implement |
| V-08 | `validation.task_alignment` | §4.4 | pre_implement |
| V-09 | `validation.artifacts` | §4.7 | pre_documenter |

---

## 7. Projections (§7)

| ID | Projection | Spec § | MUST |
|----|------------|--------|------|
| P-01 | `write_status` full replace | §7.1 | Atomic temp+rename; ISO UTC Last_sync; footer line |
| P-02 | `enrich_notes` managed keys only | §7.2 | 4 keys; no duplicate on re-sync |
| P-03 | `mirror_handoff` copy only | §7.3, §4.7 | OPTIONAL; no prose authoring |
| P-04 | Offline `status.md` | §4.3 | orchestration offline when vedaws missing |
| P-05 | Conflict: drift corrected | §7.4 | warning `projection_drift_corrected` |
| P-06 | Conflict: handoff stale | §7.4 | warning `handoff_stale` |
| P-07 | Conflict: skip_design | §7.4 | Design gate = skipped |

### status.md required columns (Bridge Spec §6.3 + Impl §7.1)

Phase, App, Handoff, Docs (submission), Orchestration, Design gate, Last_sync, Blockers — CHECK P-08

---

## 8. Recovery rules (§9)

| ID | Rule | Spec § |
|----|------|--------|
| R-01 | Map all §9.1 codes to severity | §9.1 |
| R-02 | Recovery hints for vedaws_missing, missing_manifest, bootstrap_failed, doctor_blocked, design_gate_blocked, sync_incomplete, workflow_corrupt, task_complete_denied, artifacts_missing | §9.2 |
| R-03 | CLI retry: timeout 1× immediate | §6.4, §9.3 |
| R-04 | CLI retry: spawn error 2× 100ms/500ms | §6.4 |
| R-05 | Log `recovery_retry` on retry | §6.4 |
| R-06 | MUST NOT auto-retry post_phase_complete same task >1× per correlation_id | §9.3 |
| R-07 | MUST NOT auto-destruct `.vedaws/` without human_approved_destructive_recovery | §1.2, §1.9 |

---

## 9. CLI commands — allowlist (Bridge Spec §7.1 + Impl §6)

| ID | Command | Used in operations |
|----|---------|-------------------|
| CLI-01 | `vedaws version` (ping) | dispatcher step 6 |
| CLI-02 | `vedaws init --template software [--name] --path` | bootstrap |
| CLI-03 | `vedaws doctor --path` | bootstrap, pre_implement, pre_documenter |
| CLI-04 | `vedaws status --path` | ingest, sync_status |
| CLI-05 | `vedaws workflow show --path` | bootstrap, ingest, sync, pre_implement |
| CLI-06 | `vedaws workflow activate <id> --path` | bootstrap |
| CLI-07 | `vedaws run --path` | post_implement, post_phase_complete |
| CLI-08 | `vedaws tasks complete <workflow.task> --path` | post_phase_complete, pre_documenter |
| CLI-09 | `vedaws tasks show --path` | diagnostics / snapshot |
| CLI-10 | `vedaws tasks fail ... --path` | post_phase_complete (if available) |
| CLI-11 | `vedaws state --path` | snapshot |
| CLI-12 | `vedaws state transition <state> --path` | bootstrap, ingest, post_phase_complete |
| CLI-13 | `vedaws state history --path` | recovery only |
| CLI-14 | `vedaws software artifacts --path` | pre_documenter |

**MUST:** every command includes `--path <vedaws_project_root_abs>` (§6.1)  
**MUST NOT:** any command outside allowlist without architecture review (Bridge Spec §7.1)

### CLI timeouts (§6.5)

| Class | Default | ID |
|-------|---------|-----|
| version | 10s | CLI-T01 |
| status/workflow show/state | 30s | CLI-T02 |
| doctor | 120s | CLI-T03 |
| init | 180s | CLI-T04 |
| run | 300s (manifest override) | CLI-T05 |

---

## 10. Manifest sections (§5)

| Section | Required keys | Checklist ID |
|---------|---------------|--------------|
| `[vespawd]` | `version` | MF-01 |
| `[vespawd]` | `layout` (sidecar default) | MF-02 |
| `[pos]` | `root`, `current_task`, `handoff`, `design_gate` | MF-03 |
| `[vedaws]` | `project_root`, `workflow_id`, `cli` | MF-04 |
| `[phase_map]` | OPTIONAL; overrides defaults | MF-05 |
| `[validation]` | OPTIONAL `ui_keywords` | MF-06 |
| `[compat]` | OPTIONAL `vedaws` baseline 0.5.0 | MF-07 |
| `[run]` | OPTIONAL iteration cap for post_implement | MF-08 |
| `defaults = "vespawd-sidecar-v1"` | OPTIONAL explicit flag for built-in defaults | MF-09 |

### Default phase map (merge base, §4.2 / Bridge Spec)

scope, architecture, api-design, implement, test, review, handoff — MF-10

---

## 11. Directory structure files (§2)

| Path | Required | Checklist ID |
|------|----------|--------------|
| `main/bridge/manifest.toml` | YES | DS-01 |
| `main/bridge/README.md` | YES | DS-02 |
| `main/bridge/spec/VERSION` | YES | DS-03 |
| `main/bridge/schema/manifest.schema.toml` | OPTIONAL | DS-04 |
| `main/bridge/schema/bridge_result.schema` | OPTIONAL | DS-05 |
| `main/bridge/schema/operations.schema` | OPTIONAL | DS-06 |
| `main/bridge/bin/bridge` | YES | DS-07 |
| `main/bridge/lib/api/` | YES | DS-08 |
| `main/bridge/lib/dispatcher/` | YES | DS-09 |
| `main/bridge/lib/manifest/` | YES | DS-10 |
| `main/bridge/lib/cli/` | YES | DS-11 |
| `main/bridge/lib/projection/` | YES | DS-12 |
| `main/bridge/lib/validation/` | YES | DS-13 |
| `main/bridge/lib/recovery/` | YES | DS-14 |
| `main/bridge/lib/operations/` (7 handlers) | YES | DS-15 |
| `main/bridge/lib/logging/` | YES | DS-16 |
| `main/bridge/hooks/README.md` | OPTIONAL | DS-17 |
| `main/bridge/hooks/examples/` | OPTIONAL | DS-18 |
| `main/bridge/sync/status.template.md` | YES | DS-19 |
| `main/bridge/tests/unit/` | YES | DS-20 |
| `main/bridge/tests/integration/` | YES | DS-21 |
| `main/bridge/tests/recovery/` | YES | DS-22 |
| `main/bridge/tests/fixtures/` | YES | DS-23 |

---

## 12. Error codes — complete implementation (§9.1)

All codes MUST be emit-able where spec defines:

| Code | ID |
|------|-----|
| `ok` | EC-01 |
| `vedaws_missing` | EC-02 |
| `missing_manifest` | EC-03 |
| `invalid_manifest` | EC-04 |
| `invalid_path` | EC-05 |
| `layout_conflict` | EC-06 |
| `version_mismatch` | EC-07 |
| `bootstrap_failed` | EC-08 |
| `doctor_blocked` | EC-09 |
| `doctor_warn` | EC-10 |
| `design_gate_blocked` | EC-11 |
| `design_gate_overridden` | EC-12 |
| `state_ineligible` | EC-13 |
| `state_transition_denied` | EC-14 |
| `workflow_task_mismatch` | EC-15 |
| `phase_map_miss` | EC-16 |
| `task_complete_denied` | EC-17 |
| `artifacts_missing` | EC-18 |
| `orchestration_offline` | EC-19 |
| `sync_incomplete` | EC-20 |
| `workflow_corrupt` | EC-21 |
| `cli_failed` | EC-22 |
| `cli_timeout` | EC-23 |
| `cli_spawn_error` | EC-24 |
| `internal_error` | EC-25 |
| `projection_drift_corrected` | EC-26 |
| `handoff_stale` | EC-27 |
| `recovery_retry` | EC-28 |
| `cli_ok` | EC-29 |

---

## 13. Logging requirements (§10)

| Event | Checklist ID |
|-------|--------------|
| `operation_start` | LOG-01 |
| `manifest_loaded` | LOG-02 |
| `paths_resolved` | LOG-03 |
| `cli_invoke` | LOG-04 |
| `cli_complete` | LOG-05 |
| `validation_fail` | LOG-06 |
| `projection_write` | LOG-07 |
| `operation_end` | LOG-08 |
| Correlation ID on every line | LOG-09 |
| Levels ERROR/WARN/INFO/DEBUG per §10.2 | LOG-10 |
| `duration_ms` on BridgeResult | LOG-11 |
| MUST NOT log secrets | LOG-12 |

---

## 14. Tests (§11)

### 14.1 Unit tests

| Test area | Spec § | Checklist ID |
|-----------|--------|--------------|
| manifest parse/validate/defaults | §11.1 | UT-01 |
| path resolver sidecar | §11.1 | UT-02 |
| path resolver integrated | §11.1 | UT-03 |
| phase_map keyword → id | §11.1 | UT-04 |
| projection status fields | §11.1 | UT-05 |
| projection Notes idempotency | §11.1 | UT-06 |
| design_gate validator | §11.1 | UT-07 |
| workflow_eligibility validator | §11.1 | UT-08 |
| exit code → error code mapping | §11.1 | UT-09 |
| recovery hint mapping | §11.1 | UT-10 |
| dispatcher abort on prepare failure | §1.4 | UT-11 |

**MUST NOT** require live Vedaws in unit tests (§11.1)

### 14.2 Integration tests

| Scenario | Spec § | Checklist ID |
|----------|--------|--------------|
| bootstrap empty main/ → `.vedaws/` | §11.2 | IT-01 |
| ingest → sync → pre_implement | §11.2 | IT-02 |
| post_phase_complete state change | §11.2 | IT-03 |
| pre_documenter artifacts | §11.2 | IT-04 |

**MUST NOT** modify frozen paws022/vedaws — copy fixtures (§11.2)

### 14.3 Recovery tests

| Scenario | Spec § | Checklist ID |
|----------|--------|--------------|
| re-bootstrap after partial init | §11.3 | RT-01 |
| workflow_corrupt | §11.3 | RT-02 |
| vedaws missing offline projection | §11.3 | RT-03 |
| partial sync + retry | §11.3 | RT-04 |

### 14.4 Idempotency tests

| Scenario | Spec § | Checklist ID |
|----------|--------|--------------|
| bootstrap 3× | §11.4 | ID-01 |
| sync_status 5× | §11.4 | ID-02 |
| ingest_master_prompt 2× same input | §11.4 | ID-03 |

### 14.5 Executor contract tests

| Scenario | Spec § | Checklist ID |
|----------|--------|--------------|
| Golden BridgeResult JSON per operation | §11.5 | CT-01 |
| `vedaws_commands_run` audit per §4 sequence | §11.5 | CT-02 |

---

## 15. Global MUST constraints (cross-cutting)

| ID | Requirement | Spec § |
|----|-------------|--------|
| G-01 | Single deployable unit under `main/bridge/` | §1 |
| G-02 | MUST NOT modify paws022/ or vedaws/ | Header |
| G-03 | MUST NOT write backlog or project_context | §3.5 |
| G-04 | MUST NOT hand-edit `.vedaws/` | §1.2, §6 |
| G-05 | Independent invocations; no unsafe global state | §1.3 |
| G-06 | Uncaught errors → `internal_error` BridgeResult, no crash | §3.6 |
| G-07 | Warnings alone MUST NOT set ok=false unless op defines | §3.6 |
| G-08 | Preserve logical module boundaries if flattening lib | §2 |
| G-09 | workflow_id MUST be `software` for v1 | §5.3 |
| G-10 | UTF-8 stdout/stderr capture | §6.2 |
| G-11 | Kill subprocess on timeout; no orphans | §6.5 |
| G-12 | vedaws_commands_run audit trail | §6.1 |
| G-13 | doctor_summary truncate default 2000 chars | §6.2 |

---

## 16. Dispatcher prepare pipeline steps (§1.4)

| Step | Checklist ID |
|------|--------------|
| 1. ASSIGN correlation_id | DP-01 |
| 2. LOG operation_start | DP-02 |
| 3. LOAD manifest | DP-03 |
| 4. RESOLVE paths | DP-04 |
| 5. VALIDATE layout + version | DP-05 |
| 6. VERIFY vedaws CLI (ping) | DP-06 |
| 7. ROUTE handler | DP-07 |
| 8. COLLECT results | DP-08 |
| 9. RUN projection if requested | DP-09 |
| 10. BUILD BridgeResult | DP-10 |
| 11. LOG operation_end | DP-11 |
| 12. RETURN BridgeResult | DP-12 |
| Abort 7–12 if 3–6 fail | DP-13 |

---

## 17. Operation step checklists (§4)

### OP-01 bootstrap steps 1–8 → BS-01..BS-08

### OP-02 ingest steps 1–8 → IN-01..IN-08 (+ IN-NO-RUN: no vedaws run)

### OP-03 sync steps 1–8 → SY-01..SY-08

### OP-04 pre_implement steps 1–8 → PI-01..PI-08

### OP-05 post_implement steps 1–3 → PO-01..PO-03

### OP-06 post_phase_complete steps 1–6 → PC-01..PC-06

### OP-07 pre_documenter steps 1–8 → PD-01..PD-08

---

## 18. Extension points (§12) — OPTIONAL v1

| ID | Item | Spec § |
|----|------|--------|
| E-01 | hooks/README.md contract | §12.1 |
| E-02 | after_prepare, before_cli, after_projection, on_failure hooks | §12.1 |
| E-03 | Hook MUST NOT rules | §12.1 |
| E-04 | Standalone subprocess + projection (no Vedaws plugin required) | §12.2 |
| E-05 | Backward compat: additive fields only | §12.3 |

---

## 19. Final audit template (post-implementation)

For every MUST in §15 and module tables, fill:

| Requirement ID | Requirement | Implemented? | File | Symbol | Notes |
|----------------|-------------|--------------|------|--------|-------|
| G-01 | … | | | | |

**Gate:** No phase 16 complete until all MUST rows = Yes or documented waiver with spec quote.

---

## 20. Ambiguities & conservative decisions (pre-code)

| # | Spec quote | Ambiguity | Conservative choice | Document in |
|---|------------|-----------|---------------------|-------------|
| A-01 | §5.1 step 4: defaults only if `manifest.defaults = "vespawd-sidecar-v1"` | Ship manifest without flag | Require all keys in committed `manifest.toml`; no silent defaults | `manifest.toml` |
| A-02 | §4.5 strict mode for post_implement | Where configured | `[run].strict_mode = true` in manifest | `manifest.toml` |
| A-03 | §6.3 exit code 2+ | Tool-specific | Map to `cli_failed` unless Vedaws documents otherwise | `lib/cli/exit_codes` |
| A-04 | `tasks fail` availability | May not exist in Vedaws CLI | Try invoke; on failure emit warning not blocker | `post_phase_complete` handler |
| A-05 | Impl §1.3 language | Not specified | Python 3.11+ per Vedaws | `README.md` |
| A-06 | `cli_ok` in codes table §9.1 | Success vs code | Include in codes array on success paths optionally; ok boolean primary | `BridgeResult` builder |

---

## 21. Progress tracker (fill during implementation)

| Phase | Status | Tests | MUSTs verified |
|-------|--------|-------|----------------|
| 1 Directory | done | — | Yes |
| 2 Manifest | done | UT-01 | Yes |
| 3 Public API | done | CT-01 | Yes |
| 4 Path resolver | done | UT-02 | Yes |
| 5 Logging | done | — | Yes |
| 6 CLI adapter | done | UT-09 | Yes |
| 7 Validation | done | UT-07 | Yes |
| 8 Recovery | done | RT-* | Yes |
| 9 Projection | done | UT-05,06 | Yes |
| 10 Dispatcher | done | UT-11 | Yes |
| 11 Operations | done | IT-* | Yes |
| 12 bin/bridge | done | — | Yes |
| 13 Hooks | done | — | N/A optional |
| 14 Tests | done | 26 tests | Yes |
| 15 README | done | — | Yes |
| 16 Final audit | done | BRIDGE_MUST_AUDIT.md | Yes |

---

*Checklist complete. No implementation code generated. Next step: Phase 1 — Directory structure.*
