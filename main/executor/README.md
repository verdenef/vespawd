# Vespawd Executor

IDE-neutral implementation orchestrator for Vespawd. Invokes the Bridge via its public CLI (`main/bridge/bin/bridge`); does not import Bridge internals.

## Phase 1 (complete)

- Workspace discovery and path resolution (Executor Spec §3.5)
- Master Prompt trigger detection (§3.1)
- Startup validation (§3.4)
- Startup sequence: `bootstrap` + `sync_status` (§3.6–3.7)

## Phase 8 (complete)

- `build_report()` / `ExecutorReport` — §10.7 report to user (what changed, run/test, HANDOFF, next action, handoff-ready signal)
- `append_task_note()` — §11.5/§12.5 orchestration-error and debugging notes (idempotent)
- `read_resume_state()` / `ResumeState` — §12.3 resume mid-phase (read current_task/status/project_context)
- Tool neutrality (§14) enforced by source-level import checks

## Phase 7 (complete)

- `orchestrate_completion()` — full §5.4 sequence (phase complete → HANDOFF refresh → completed log → task close-out)
- `orchestrate_pre_documenter()` — §8.5 documenter gate via public `pre_documenter`
- `refresh_handoff()` / `HandoffFacts` — §13 full HANDOFF refresh (facts-only, idempotent)
- `write_completed_log()` — §10.6 `tasks/completed/YYYY-MM-DD-slug.md`

## Phase 6 (complete)

- `check_changed_paths()` / `classify_path()` — §7.1/§7.2 allowed vs forbidden userspace policy (layout-aware)
- `append_progress_entry()` — §8.3 Progress Log files-changed summary (idempotent)
- `orchestrate_post_implement()` — §7 guard + §8.3 hooks (`post_implement` → `sync_status`)

## Phase 5 (complete)

- `run_pre_implement_check()` — §8.2 gate via public `pre_implement_check`
- Surfaces design gate, workflow eligibility, task mismatch, doctor, recovery
- Blocks userspace implementation when Bridge reports blocking codes

## Phase 4 (complete)

- `orchestrate_master_prompt_from_text()` — full §5.3 sequence (PAWS → ingest → sync → HANDOFF)
- `orchestrate_phase_complete()` — §5.4 steps 2–3 (post_phase_complete → sync_status)
- Bridge via public CLI only; recovery hints surfaced in orchestration results

## Phase 3 (complete)

- PAWS writers: `project_context.md` merge, `current_task.md`, `backlog.md` append, HANDOFF seed
- `sync_paws_files()` orchestrates §5.3 steps 1 and 4 (no Bridge calls)
- Idempotent re-sync for all artifacts

## Phase 2 (complete)

- Master Prompt parsing (Executor Spec §4)
- Section split, CURRENT TASK / context / backlog / instructions parsers
- Parse failure handling (§4.7)
- `parse_master_prompt()` + `to_ingest_payload()` for Phase 4 Bridge ingest

## CLI

```bash
python main/executor/bin/executor startup --workspace /path/to/vespawd
```

## Tests

```bash
cd main/executor
python -m pytest -q
```

## Package

Python package: `vespawd_executor` under `lib/`.
