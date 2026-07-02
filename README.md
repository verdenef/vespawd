# Vespawd

**Vespawd is a hybrid Development Operating System** that keeps [PAWS](paws022/) as the human-facing agent workflow (planner → executor → documenter) and adds [Vedaws](vedaws/) as the executable orchestration runtime underneath the application workspace.

> **PAWS decides what humans and agents say. Vedaws decides what may run next. Your IDE still writes the app.**

Vespawd is designed for **chat-first development**: you turn an assignment into working software by looping *Planner → paste into your IDE → test → Planner again*. Vedaws runs in the background and handles the bookkeeping PAWS used to leave to you — phase order, status sync, health checks, and artifact checklists.

---

## What Vespawd is

Vespawd unifies two previously independent systems **without forking either one**:

- **PAWS** provides the proven, human-legible agent contracts: the `# POS MASTER PROMPT` planner format, executor coding rules, the documenter pipeline, and markdown project memory.
- **Vedaws** provides an executable runtime: a project state machine, workflow/task dependencies, worker dispatch, automation, health diagnostics, and AI capability routing.

The integration lives entirely in a new **Bridge** layer under `main/`. The Bridge translates POS conventions into Vedaws orchestration and keeps both views consistent, so neither frozen reference tree is modified.

---

## Key features

- **IDE-neutral executor** — an implementation orchestrator that parses the Master Prompt, maintains PAWS memory files, and drives the Bridge. It contains no vendor-specific imports or terminology and works the same across Cursor, VS Code, Windsurf, JetBrains AI, and others.
- **Public-CLI Bridge** — a standalone sync layer between PAWS (`paws022/`) and Vedaws (`main/.vedaws/`), invoked purely as a subprocess. Operations: `bootstrap`, `ingest_master_prompt`, `sync_status`, `pre_implement_check`, `post_implement`, `post_phase_complete`, `pre_documenter`.
- **Design + doctor gates** — implementation is blocked until design artifacts are ready and orchestration eligibility is satisfied, enforced through the Bridge's `pre_implement_check`.
- **Idempotent PAWS synchronization** — writers for `project_context.md`, `current_task.md`, `backlog.md`, and `HANDOFF_FOR_DOCUMENTER.md` produce stable output on repeated runs.
- **Vedaws orchestration runtime** — project lifecycle state, `software` workflow (`scope → architecture → api-design → implement → test → review → handoff`), capability-based worker routing, event-driven automation, and `vedaws doctor` diagnostics.
- **Human approval gate** — Vespawd waits for you to test and approve between planner phases; the executor implements, you verify.
- **Preserved academic workflow** — the documenter reads `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` only, keeping the submission/rubric flow intact.

---

## High-level architecture

```
                    HUMAN / EXTERNAL AGENTS
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    Planner (PAWS)     UI designer (PAWS)    Documenter (PAWS)
         │                    │                    │
         ▼                    ▼                    ▼
  POS MASTER PROMPT      design/DESIGN.md    HANDOFF + rubric
         │                    │                    │
         └────────────┬───────┴────────────────────┘
                      ▼
              IDE EXECUTOR (PAWS rules)
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   paws022/       main/bridge    main/src/
   memory +       (sync +        userspace
   scheduler      invoke)        (your app)
   (markdown)          │
                       ▼
                 vedaws CLI ──► .vedaws/ in main/
                 (runtime)     state, workflow,
                               dispatch, automation
```

- **Control flow:** Vedaws decides eligibility — which task may be active and whether a run proceeds.
- **Data flow:** PAWS markdown remains what agents read for context.
- **Your IDE** is the only component that writes application code.

Full design detail: [`main/docs/VESPAWD_ARCHITECTURE.md`](main/docs/VESPAWD_ARCHITECTURE.md).

---

## Repository structure

```
vespawd/                          ← workspace root (open in your IDE)
├── main/                         ← Vespawd application, Bridge, and Executor
│   ├── bridge/                   ← PAWS ↔ Vedaws sync layer (public CLI)
│   ├── executor/                 ← IDE-neutral implementation orchestrator
│   └── docs/                     ← architecture, specifications, audits
├── paws022/                      ← PAWS kernel + POS memory (frozen reference)
│   ├── .ai/                      ← planner / executor / documenter prompts + rules
│   ├── tasks/                    ← intake, current_task, backlog, completed
│   ├── docs/                     ← project memory + HANDOFF
│   └── design/                   ← UI design contract
└── vedaws/                       ← Vedaws orchestration runtime (frozen reference)
    ├── runtime/                  ← state, workflow, dispatch, automation, AI
    ├── plugins/                  ← software / git / unity / mock plugins
    └── tests/                    ← runtime test suite
```

`paws022/` and `vedaws/` are **frozen references**: Vespawd integrates them without modifying either tree. All new behavior lives under `main/`.

---

## Create a new project

Keep one copy of the Vespawd framework on your machine (this repo, cloned from git). For each new application, run the setup script — it copies the framework into your project and wires the sidecar layout automatically.

**Interactive (recommended):**

```powershell
# Windows
.\scripts\new-vespawd-project.ps1
```

```bash
# macOS / Linux
./scripts/new-vespawd-project.sh
```

The script prompts for:
- **Parent directory** — where to create the project (e.g. `C:\dev`)
- **Project name** — folder name, product name, and Vedaws project name
- **Confirmation** — shows the layout before copying

**Non-interactive:**

```bash
python scripts/new_project.py C:\dev\my-todo-app --name my-todo-app --yes
```

**What you get:**

```
my-todo-app/                 ← open THIS in your IDE
├── vespawd/                 ← framework copy (paws022, vedaws, bridge, executor)
│   ├── paws022/             ← project memory (tasks, docs, agent rules)
│   └── main/
│       ├── bridge/
│       ├── executor/
│       └── .vedaws/         ← orchestration state (auto-managed)
└── main/
    └── src/                 ← your application code
```

The script also: resets PAWS memory to a clean slate, runs `vedaws init`, optionally `git init` + `.gitignore`, and verifies executor startup.

Flags: `--force` (replace existing `vespawd/`), `--no-init`, `--no-git`, `--no-verify`.

---

## Installation

Vespawd requires **Python 3.11+**.

### 1. Install the Vedaws runtime (once per machine)

```bash
cd vedaws
pip install -e ".[dev]"
vedaws version
```

### 2. Install the Bridge (for tests / development)

```bash
cd main/bridge
pip install -e ".[dev]"
```

The Bridge locates the Vedaws CLI on `PATH` or via `[vedaws].cli` in `main/bridge/manifest.toml`.

### 3. Configure external agents

Copy the planner instructions from `paws022/.ai/planner_prompt.md` into your planner chat (ChatGPT, Claude, or a Gemini Gem), and `paws022/.ai/documenter_prompt.md` into a separate documenter chat. See [`paws022/docs/EXTERNAL_AGENTS_SETUP.md`](paws022/docs/EXTERNAL_AGENTS_SETUP.md) for details.

---

## Quick Start

Open the **workspace root** (the folder containing `main/`, `paws022/`, and `vedaws/`) in your IDE.

```bash
# 1. Bootstrap orchestration for a project (once per project)
cd main
vedaws init --template software --name my-project

# 2. Dump your assignment into raw intake
#    → edit paws022/tasks/intake.md

# 3. Ask your Planner to produce a POS MASTER PROMPT from the intake

# 4. In your IDE agent chat, send "Execute this." then paste the Master Prompt.
#    The executor updates PAWS files and writes code in main/src/.

# 5. Test the app, then loop back to the Planner for the next phase.
```

The executor CLI exposes the startup command directly; orchestration is available through the library API (`vespawd_executor.api`):

```bash
python main/executor/bin/executor startup --workspace /path/to/vespawd
```

Diagnostics (run only when the executor or status tells you to):

```bash
vedaws doctor  --path main    # is the project healthy?
vedaws status  --path main    # what phase is orchestration on?
vedaws software artifacts --path main   # are documentation artifacts present?
```

---

## Typical workflow

The main loop is **Planner → IDE → test → Planner**, repeated until the backlog is empty.

1. **Intake** — paste the assignment and rubric into `paws022/tasks/intake.md`.
2. **Plan** — the Planner turns intake into a `# POS MASTER PROMPT` (Phase 1 in `CURRENT TASK`, later phases in `BACKLOG`).
3. **Execute** — paste the Master Prompt into your IDE with `Execute this.`. The executor parses it, syncs PAWS memory, runs the design/doctor gates via the Bridge, and implements in `main/src/`.
4. **Verify** — you run and test the app. Small fixes stay in IDE chat; a completed phase goes back to the Planner.
5. **Advance** — a planner follow-up (see `paws022/.ai/planner_followup_message.md`) produces the next Master Prompt.
6. **Handoff** — the executor refreshes `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` (facts only) and the Bridge runs the `pre_documenter` gate.
7. **Document** — paste the HANDOFF plus your rubric into the Documenter to write the submission report.

New to the project? Read [`main/docs/START_HERE.md`](main/docs/START_HERE.md) for a step-by-step walkthrough.

---

## Design principles

1. **Do not fork PAWS or Vedaws.** Frozen trees remain comparable references; Vespawd evolves only in `main/`.
2. **The POS MASTER PROMPT stays the planner contract.** External planners are unchanged.
3. **The IDE remains the implementation executor.** Vedaws workers supplement, not replace, IDE agents for application code.
4. **Vedaws state is orchestration authority.** Formal eligibility, dependencies, and an audit trail.
5. **PAWS files stay human-legible.** Agents and users read markdown, not TOML.
6. **The Bridge synchronizes; neither tree owns the other.**
7. **Tool neutrality.** The executor behaves identically regardless of IDE, with no vendor-specific imports or terminology.
8. **Idempotency.** Writers and orchestration steps produce consistent state on repeated execution.

---

## Documentation and specifications

All authoritative documents live under [`main/docs/`](main/docs/):

| Topic | Document |
|-------|----------|
| Getting started (users) | [`START_HERE.md`](main/docs/START_HERE.md) |
| Architecture | [`VESPAWD_ARCHITECTURE.md`](main/docs/VESPAWD_ARCHITECTURE.md) |
| PAWS vs Vedaws comparison | [`PAWS_VS_VEDAWS_ANALYSIS.md`](main/docs/PAWS_VS_VEDAWS_ANALYSIS.md) |
| Bridge specification | [`VESPAWD_BRIDGE_SPEC.md`](main/docs/VESPAWD_BRIDGE_SPEC.md) |
| Bridge implementation spec | [`BRIDGE_IMPLEMENTATION_SPEC.md`](main/docs/BRIDGE_IMPLEMENTATION_SPEC.md) |
| Executor specification | [`VESPAWD_EXECUTOR_SPEC.md`](main/docs/VESPAWD_EXECUTOR_SPEC.md) |
| Planner specification | [`PLANNER_SPEC.md`](main/docs/PLANNER_SPEC.md) |
| Bridge integration validation | [`BRIDGE_INTEGRATION_VALIDATION.md`](main/docs/BRIDGE_INTEGRATION_VALIDATION.md) |
| Executor final validation | [`EXECUTOR_FINAL_VALIDATION.md`](main/docs/EXECUTOR_FINAL_VALIDATION.md) |

Component READMEs: [`main/bridge/README.md`](main/bridge/README.md), [`main/executor/README.md`](main/executor/README.md), [`vedaws/README.md`](vedaws/README.md).

---

## Current project status

- **Bridge** — implementation complete; integration validation passed.
- **Executor** — all implementation phases (1–8) complete; final production audit verdict is production-ready.
- **Vedaws runtime** — provides the state machine, `software` workflow, plugins (software, git, unity, mock), workers, and diagnostics used by Vespawd v1.

Run the test suites:

```bash
# Bridge
cd main/bridge && pytest

# Executor
cd main/executor && python -m pytest -q

# Vedaws runtime
cd vedaws && pytest
```

---

## Contributing

- All new Vespawd behavior belongs under `main/`. Do **not** modify the frozen `paws022/` or `vedaws/` reference trees.
- Interact with the Bridge only through its public CLI (`main/bridge/bin/bridge`); do not import Bridge internals.
- Preserve tool neutrality in the executor — no IDE-specific imports or terminology.
- Keep writers and orchestration steps idempotent.
- Follow the relevant specification in `main/docs/` and run the test suites before submitting changes.

---

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 verdenef.
