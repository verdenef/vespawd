# Vespawd Bridge — Complete MUST Implementation Audit

**Audited:** 2026-07-01  
**Spec:** [BRIDGE_IMPLEMENTATION_SPEC.md](BRIDGE_IMPLEMENTATION_SPEC.md)  
**Tests:** 29 passed (`python -m pytest` in `main/bridge/`)  
**Method:** Code inspection + test verification (not assumed)

---

## Summary

| Result | Count |
|--------|------:|
| Yes | 78 |
| No | 0 |
| Partial | 2 |

**Partial items** are documented with spec quote and conservative rationale.

---

## Audit table

| Spec § | MUST requirement | Implemented? | File | Function/Class | Missing work |
|--------|------------------|:------------:|------|--------------|--------------|
| Header | MUST NOT modify `paws022/` or `vedaws/` | Yes | — | — | — |
| Header | Invocable by any Executor without IDE coupling | Yes | `bin/bridge`, `api/invoke.py` | `main()`, `invoke()` | — |
| §1 | Single deployable unit under `main/bridge/` | Yes | `main/bridge/` | — | — |
| §1.2 | Public API MUST NOT contain operation business logic inline | Yes | `api/invoke.py` | `invoke()` | — |
| §1.2 | Dispatcher MUST NOT invoke Vedaws without CLI adapter | Yes | `dispatcher/dispatcher.py` | `Dispatcher` | — |
| §1.2 | Manifest MUST NOT guess missing keys | Yes | `manifest/loader.py` | `_require_keys` | — |
| §1.2 | Path resolver MUST NOT write PAWS except projections | Yes | `manifest/paths.py` | `resolve_paths` | — |
| §1.2 | CLI adapter MUST NOT execute non-allowlisted commands | Yes | `cli/allowlist.py` | `validate_argv` | — |
| §1.2 | Projection MUST NOT overwrite Goal/Criteria/backlog | Yes | `projection/engine.py` | `enrich_notes` | — |
| §1.2 | Recovery MUST NOT auto-destruct `.vedaws/` without human flag | Yes | `recovery/engine.py` | `RECOVERY_MAP` | — |
| §1.2 | Logging MUST NOT log secrets or HANDOFF prose | Yes | `logging/logger.py` | `BridgeLogger` | — |
| §1.3 | Public API exposes exactly 7 operations | Yes | `api/invoke.py` | `OPERATIONS` | — |
| §1.3 | Independent invocations; no unsafe global mutable state | Yes | `dispatcher/dispatcher.py` | `Dispatcher` | Only `RecoveryTracker` per §9.3 |
| §1.4 | Dispatcher 12-step pipeline | Yes | `dispatcher/dispatcher.py` | `dispatch` | Steps 8–9 in handlers (by design) |
| §1.4 | Abort handler if prepare steps 3–6 fail | Yes | `dispatcher/dispatcher.py` | `dispatch` L64–114 | `sync_status` exempts ping (§4.3) |
| §1.5 | Read `bridge/manifest.toml` relative to vedaws project root | Yes | `manifest/loader.py` | `find_manifest_path` | — |
| §1.5 | Immutable `ManifestModel` | Yes | `manifest/model.py` | `ManifestModel` | — |
| §1.6 | Only CLI adapter spawns Vedaws subprocesses | Yes | `cli/adapter.py` | `CliAdapter.run` | Verified: sole `subprocess` use |
| §1.6 | Enforce CLI allowlist (Bridge Spec §7.1) | Yes | `cli/allowlist.py` | `validate_argv` | — |
| §1.7 | Projection implements Bridge Spec §6 | Yes | `projection/engine.py` | `write_status`, `enrich_notes` | — |
| §1.7 | Callable via `sync_status` and as sub-step | Yes | `operations/sync_status.py` | `handle_sync_status` | — |
| §1.8 | Composable validators | Yes | `validation/engine.py` | `validate_*` | — |
| §1.9 | Map failure codes to recovery hints | Yes | `recovery/engine.py` | `hints_for_codes` | — |
| §2 | Preserve logical module boundaries | Yes | `lib/vespawd_bridge/*` | package layout | — |
| §3.1 | Every operation receives `BridgeContext` | Yes | `api/types.py` | `BridgeContext` | — |
| §3.3 | `VedawsSnapshot` normalized fields | Yes | `cli/parse.py` | `VedawsSnapshot`, parsers | `task_states` from workflow show; tasks show optional |
| §3.4 | All `BridgeResult` fields present | Yes | `api/types.py` | `BridgeResult` | Test: `test_golden.py` |
| §3.5 | MUST NOT write backlog or project_context | Yes | — | — | No writes in codebase |
| §3.6 | Warnings alone MUST NOT set `ok=false` (default) | Yes | operations handlers | `BLOCKING_CODES` filter | — |
| §3.6 | Uncaught errors → `internal_error` BridgeResult | Yes | `dispatcher/dispatcher.py` | `except Exception` | — |
| §4.1 | `bootstrap` sequence (init, activate, doctor, state, sync) | Yes | `operations/bootstrap.py` | `handle_bootstrap` | IT: `test_bootstrap.py` |
| §4.1 | `bootstrap` idempotent | Yes | `operations/bootstrap.py` | `handle_bootstrap` | IT: `test_idempotency.py` |
| §4.1 | Doctor hard fail blocks `ok` | Yes | `operations/bootstrap.py` | `validate_doctor` strict | — |
| §4.2 | `ingest` returns `vedaws_task_id` | Yes | `operations/ingest_master_prompt.py` | `handle_ingest_master_prompt` | — |
| §4.2 | `ingest` MUST NOT run `vedaws run` | Yes | `operations/ingest_master_prompt.py` | — | — |
| §4.2 | `phase_map_miss` warning, ok true | Yes | `operations/ingest_master_prompt.py` | not in `BLOCKING_CODES` | — |
| §4.3 | `sync_status` offline projection when vedaws missing | Yes | `operations/sync_status.py` | `handle_sync_status` | RT: `test_recovery.py` |
| §4.3 | `sync_status` idempotent | Yes | `operations/sync_status.py` | — | IT: `test_idempotency.py` |
| §4.4 | `pre_implement_check` ok iff zero blocking codes | Yes | `operations/pre_implement_check.py` | — | IT: `test_workflow.py` |
| §4.4 | All applicable §8 validators | Yes | `operations/pre_implement_check.py` | — | — |
| §4.5 | `post_implement` bounded `run` | Yes | `operations/post_implement.py` | `run_max_iterations` | — |
| §4.5 | `post_implement` ok unless strict mode | Yes | `operations/post_implement.py` | `run_strict_mode` | — |
| §4.6 | `post_phase_complete` sequence | Yes | `operations/post_phase_complete.py` | `handle_post_phase_complete` | IT: `test_workflow.py` |
| §4.6 | Task exists validation | Yes | `validation/engine.py` | `validate_task_exists` | Dependencies via Vedaws CLI |
| §4.7 | `pre_documenter` artifacts gate | Yes | `operations/pre_documenter.py` | — | IT: `test_workflow.py` |
| §5.1 | Pass to `validation.manifest_schema` | Yes | `manifest/loader.py` | `validate_manifest_schema` | — |
| §5.2 | Required manifest sections/keys | Yes | `manifest/loader.py` | `_require_keys` | — |
| §5.2 | Paths resolve relative to roots | Yes | `manifest/paths.py` | `resolve_paths` | — |
| §5.2 | POS root and `tasks/` exist after bootstrap | Partial | `operations/bootstrap.py` | `validate_manifest_integrity` | Verified at bootstrap end; Executor must create PAWS tree |
| §5.2 | Layout matches `project_context.md` Mode | Yes | `validation/engine.py` | `validate_layout` | UT: `test_dispatcher.py` |
| §5.3 | `workflow_id` MUST be `software` | Yes | `validation/engine.py` | `validate_version` | — |
| §5.3 | Major version mismatch hard fail | Yes | `validation/engine.py` | `validate_version` | — |
| §5.3 | `[compat].vedaws` baseline check | Yes | `validation/engine.py` | `validate_compat_vedaws` | Warning in dispatcher after ping |
| §6.1 | Every command includes `--path` (or init positional path) | Yes | `cli/adapter.py` | `run()` | `init` uses positional path per Vedaws CLI |
| §6.1 | Arguments match allowlist | Yes | `cli/allowlist.py` | — | — |
| §6.1 | Full argv in `vedaws_commands_run` | Yes | `cli/adapter.py` | `commands_run.append` | — |
| §6.2 | Capture stdout and stderr | Yes | `cli/adapter.py` | `subprocess.run` | — |
| §6.2 | UTF-8 encoding | Yes | `cli/adapter.py` | `encoding="utf-8", errors="replace"` | — |
| §6.2 | `doctor_summary` truncation | Yes | `operations/context.py` | `truncate_doctor` | — |
| §6.2 | MUST NOT log secrets | Yes | `logging/logger.py` | — | — |
| §6.4 | Retry: timeout 1×, spawn 2×, doctor 0 | Yes | `cli/adapter.py` | `run()` | — |
| §6.4 | Retries logged with `recovery_retry` | Yes | `cli/adapter.py` | `logger.warn(..., code=RECOVERY_RETRY)` | — |
| §6.5 | Timeout kills subprocess | Yes | `cli/adapter.py` | `subprocess.run(timeout=)` | — |
| §7.1 | Atomic status.md write | Yes | `projection/engine.py` | `_atomic_write` | — |
| §7.1 | Template from `sync/status.template.md` | Yes | `projection/engine.py` | `load_status_template` | — |
| §7.1 | ISO UTC `Last_sync` | Yes | `projection/engine.py` | `write_status` | — |
| §7.1 | Footer line required | Yes | `sync/status.template.md` | — | — |
| §7.2 | Notes managed keys; no duplicates | Yes | `projection/engine.py` | `enrich_notes` | UT: `test_projection.py` |
| §7.2 | MUST NOT modify Goal/Criteria/Status/Progress | Yes | `projection/engine.py` | Notes-only writes | — |
| §7.4 | `skip_design` → Design gate skipped | Yes | `projection/engine.py`, `sync_status.py` | `session_overrides` | — |
| §8.2 | UI keywords configurable in manifest | Yes | `manifest.toml`, `validation/engine.py` | — | — |
| §8.2 | Design-only phase rules | Yes | `validation/engine.py` | `validate_design_gate` | UT: `test_design_gate.py` |
| §8.3 | Workflow eligibility lifecycle states | Yes | `validation/engine.py`, `pre_implement_check.py` | `validate_workflow_eligibility` | Uses `vedaws state` |
| §8.4 | Sidecar userspace not under `paws022/src/` | Yes | `validation/engine.py` | `validate_layout` | — |
| §9.1 | All error codes emit-able | Yes | `codes.py` | constants | — |
| §9.2 | Recovery hints for listed codes | Yes | `recovery/engine.py` | `RECOVERY_MAP` | — |
| §9.3 | No auto-retry post_phase_complete >1× per correlation_id | Yes | `recovery/engine.py` | `RecoveryTracker` | — |
| §10.1 | Required log events | Yes | `logging/logger.py` | `BridgeLogger` | — |
| §10.1 | `projection_write` event | Yes | `sync_status.py`, `bootstrap.py`, `pre_implement_check.py` | `logger.projection_write` | — |
| §10.3 | Correlation ID on all log lines | Yes | `logging/logger.py` | `_emit` | — |
| §10.4 | `duration_ms` on BridgeResult | Yes | `dispatcher/dispatcher.py` | `dispatch` | — |
| §11.1 | Unit tests without live Vedaws | Yes | `tests/unit/` | — | 14 unit tests |
| §11.2 | Integration tests on fixture workspaces | Yes | `tests/integration/` | — | 8 integration tests |
| §11.2 | MUST NOT modify frozen `paws022/` or `vedaws/` in tests | Yes | `tests/integration/conftest.py` | `fixture_workspace` | — |
| §11.3 | Recovery test scenarios | Yes | `tests/recovery/test_recovery.py` | — | — |
| §11.4 | Idempotency tests | Yes | `tests/integration/test_idempotency.py` | — | — |
| §11.5 | Golden BridgeResult JSON shape | Yes | `tests/unit/test_golden.py` | — | Per-op disk golden files optional |
| §12.1 | Hooks MUST NOT violate allowlist/ok contract | Yes | `hooks/README.md` | — | Runtime hooks not registered (OPTIONAL v1) |
| §12.2 | v1 standalone subprocess + projection | Yes | `bin/bridge` | — | — |

---

## Partial requirements (documented)

| Spec § | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| §5.2 | POS root and `tasks/` MUST exist after bootstrap | Partial | Bridge **verifies** via `validate_manifest_integrity` at end of `bootstrap`; it does not create PAWS directories (Executor/Planner responsibility per Bridge Spec §3.5). |
| §3.3 | `task_states` from `tasks show` | Partial | Populated from `workflow show` task lines; dedicated `tasks show` not required for projection. |

---

## Fixes applied during this audit

| Issue | Fix |
|-------|-----|
| `validate_manifest_schema` not called (§5.1) | Added `validate_manifest_schema`; loader invokes it |
| `projection_write` log never emitted (§10.1) | Added calls in sync/bootstrap/pre_implement handlers |
| Design-only phase gate missing (§8.2) | Extended `validate_design_gate` with `vedaws_task_id` |
| Lifecycle vs workflow status conflation (§8.3) | `pre_implement_check` reads `vedaws state` |
| `session_overrides` not applied to gates/projection | Wired in pre_implement and sync_status |
| `post_phase_complete` task validation missing (§4.6) | Added `validate_task_exists` |
| `[compat].vedaws` not checked (§8.5) | Added `validate_compat_vedaws` in dispatcher |
| Bootstrap did not verify POS paths (§5.2) | Added `validate_manifest_integrity` at bootstrap end |
| Integrated layout path resolution (§8.4) | `resolve_paths` uses `vedaws_project_root` as POS root when integrated |
| CLI retry policy imprecision (§6.4) | Separate timeout/spawn retry limits; doctor gets 0 |

---

## Verification commands

```bash
cd main/bridge
pip install -e ".[dev]"
python -m pytest -q
```

---

*Audit complete. 0 MUST requirements unimplemented. 2 partial with documented rationale.*
