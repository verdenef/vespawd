# POS ADOPT BOOTSTRAP

> **Copy everything below the line into your executor IDE chat** (Cursor, Copilot, etc.) right after running `pos-adopt.ps1`.  
> Open the **adopted project folder** as the workspace first.

---

## USER REQUEST

I just added POS (paws022) to this **existing** repository. The script created skeleton files; they are mostly empty or placeholders.

**Your job now:** inventory this codebase and **fill POS memory** from what you find. Do **not** implement new features or refactor application code in this pass.

## EXECUTOR INSTRUCTIONS

1. Read POS rules: `.ai/executor_rules.md`, then scan the repo (README, `src/`, config files, dependency manifests, existing `docs/`, env examples).

2. **Update these files** with factual content (replace `_TBD_` / placeholders where you have evidence; leave `_TBD_` only when unknown):
   - `.ai/project_context.md` — product name, summary, stack (language, framework, **MySQL** if applicable), layout mode, how to run/test, env vars, agent notes
   - `docs/architecture.md` — components, data flow, key paths
   - `docs/db_schema.md` — tables/entities if inferrable (MySQL-oriented)
   - `docs/api_contracts.md` — routes/endpoints if inferrable; otherwise note “none yet”
   - `docs/HANDOFF_FOR_DOCUMENTER.md` — factual bullets for a documenter (no report prose)
   - `tasks/status.md` — phase: `adopt-bootstrap`, app status, handoff freshness date

3. **Do not overwrite** user-written content blindly — merge and improve. If a file already has real content, extend it rather than replacing with generic template text.

4. **Do not modify** application source under `src/` (or the app folder named in `project_context.md`) except reading for analysis.

5. Set `tasks/current_task.md` to a short **completed** bootstrap task, or `Status: ready` with goal: “POS memory filled from repo; awaiting assignment via POS MASTER PROMPT.”

6. Reply with a brief summary: what you filled, what remains `_TBD_`, and tell me to use **planner** for the next real task.

**Execute immediately.**
