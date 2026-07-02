# PAWS vs Vedaws — Factual Comparison

**Purpose:** Early design reference for Vespawd.  
**Sources:** Frozen reference trees `paws022/` and `vedaws/` only.  
**Date:** 2026-07-01  

This document describes what each system *is*, based on files present in those repositories. It does not propose a Vespawd design or invent features not evidenced in the sources.

---

## Repository snapshot (this workspace)

| Tree | Contents observed |
|------|-------------------|
| `paws022/` | Markdown templates, agent prompts, task/docs scaffolds, Cursor rules. **No** `src/`, **no** Python/JS/PS1 executables in this copy. Docs reference `scripts/`, `setup/`, `BOOTSTRAP.md`, `START.md` that are **not present** here. |
| `vedaws/` | Full Python runtime (`runtime/vedaws/`), CLI, plugins, workers, tests (121 integration tests cited in `VEDAWS_BOOTSTRAP.md`). |
| `main/` | New Vespawd project (this document is its first artifact). |

---

## 1. What PAWS is

**PAWS** (folder name `paws022`) is the **Project Operating System (POS)** — a **document- and prompt-driven template** for organizing AI-assisted software projects.

From `paws022/AGENTS.md`:

> This repository uses the **Project Operating System**. All coding agents should follow `.ai/executor_rules.md`.

POS defines four layers (`paws022/.ai/system_prompt.md`, `paws022/.ai/executor_rules.md`):

| Layer | Path | Role |
|-------|------|------|
| **Kernel** | `.ai/` (except `project_context.md`) | Reusable agent rules, prompts, workflows |
| **Memory** | `project_context.md`, `docs/` | Project-specific facts (stack, architecture, schema, ADRs) |
| **Scheduler** | `tasks/` | Active work (`current_task.md`), backlog, completed log |
| **Userspace** | `src/` or sidecar app folder | Application implementation |

POS is **tool-neutral** (`paws022/docs/TOOLCHAIN.md`): it specifies roles and file contracts, not a single IDE or AI vendor. Version tracked as `instructionsVersion` (e.g. `1.1.7` in `paws022/docs/UPDATING.md`).

POS supports two layouts (`paws022/docs/PROJECT_LAYOUT.md`):

- **Integrated** — POS folders and app code share the repo root.
- **Sidecar** — POS lives in `paws022/` beside an app folder such as `main/` (the layout used by this Vespawd workspace).

---

## 2. What problem PAWS solves

PAWS addresses **coordination of AI-assisted development without a shared runtime** — especially for coursework and small teams where the developer manually stitches planner, executor, and documenter tools.

Evidence from workflow docs:

- `paws022/docs/LAZY_WORKFLOW.md` — pipeline: assignment → planner → POS MASTER PROMPT → executor → HANDOFF → documenter.
- `paws022/docs/EXECUTOR_LOOP.md` — planner produces prompts; executor writes task files and code; human tests between phases.
- `paws022/.ai/planner_prompt.md` — planner **does not write implementation code**; output is a structured handoff to the executor.

The implicit problem: without POS, agents lack a **consistent read order**, **single active task**, **project memory location**, and **submission handoff format**. POS standardizes those as files in the repo.

---

## 3. Strengths of PAWS

1. **Low adoption friction** — Markdown + prompts only; no runtime install required in the frozen `paws022/` copy.
2. **Clear role boundaries** — Planner, executor, documenter, optional UI designer are separated (`paws022/docs/TOOLCHAIN.md`, `paws022/.ai/planner_prompt.md`, `paws022/.ai/documenter_prompt.md`).
3. **Structured intake** — POS MASTER PROMPT format with PROJECT BRIEF, CURRENT TASK, BACKLOG, EXECUTOR INSTRUCTIONS (`paws022/.ai/planner_prompt.md`).
4. **Executor automation contract** — Master Prompt paste auto-writes `tasks/current_task.md`, merges context, seeds HANDOFF (`paws022/.ai/executor_rules.md`).
5. **Persistent project memory** — Canonical locations for architecture, API contracts, DB schema, ADRs (`paws022/docs/architecture.md`, `api_contracts.md`, `db_schema.md`, `decisions.md`).
6. **UI design artifact contract** — `design/DESIGN.md` gate before implementing screens (`paws022/docs/UI_DESIGN.md`, `paws022/design/README.md`).
7. **Academic submission pipeline** — Phased report writing from HANDOFF + rubric (`paws022/docs/SUBMISSION_DOCUMENTATION.md`).
8. **IDE portability** — `AGENTS.md`, `executor_rules.md`, `.cursor/rules/pos.mdc` work across Cursor, VS Code, Windsurf, etc. (`paws022/docs/TOOLCHAIN.md`).
9. **Adopt-existing-project path** — POS can wrap existing code without moving `src/` (`paws022/docs/ADOPT_EXISTING_PROJECT.md`).
10. **Kernel vs memory separation** — Template rules stay in `.ai/`; product facts in `project_context.md` and `docs/` (`paws022/.ai/README.md`).

---

## 4. Weaknesses of PAWS

1. **No executable orchestration** — Progress depends on humans pasting prompts and agents voluntarily following markdown rules. There is no enforcement loop in `paws022/`.
2. **Human as runtime** — Phase transitions, backlog pulls, and status updates are manual unless an executor agent complies (`paws022/tasks/status.md` is a template expecting executor updates).
3. **Incomplete reference copy** — This workspace's `paws022/` lacks `scripts/`, `setup/`, `src/`, `BOOTSTRAP.md`, and `START.md` referenced throughout docs (`paws022/.ai/README.md`, `paws022/docs/UPDATING.md`, `paws022/docs/PROJECT_LAYOUT.md`).
4. **External agent setup burden** — Planner/documenter prompts must be copied into Gemini/ChatGPT/Claude manually; updates are not automatic (`paws022/docs/EXTERNAL_AGENTS_SETUP.md`, `paws022/docs/UPDATING.md` — "Still manual: re-copy planner/documenter prompts").
5. **No formal state machine** — Task status is free-text (`idle` | `in_progress` | `blocked` in `paws022/tasks/current_task.md`); no transition rules or eligibility engine.
6. **No worker abstraction** — Cannot declare capabilities, dispatch work, or verify artifact presence programmatically.
7. **No automation engine** — Repetitive coordination (e.g. run tests after implement) is not rule-driven.
8. **Placeholder-heavy bootstrap** — Fresh template ships with `_TBD_` fields (`paws022/.ai/project_context.md`, `paws022/docs/architecture.md`).
9. **Single-database bias in planner** — Planner defaults to MySQL unless user states otherwise (`paws022/.ai/planner_prompt.md`); not wrong, but encodes an opinion in the kernel prompt.
10. **Scaling limits** — Synchronous human-in-the-loop per phase; no parallel task dispatch or event integration.

---

## 5. What Vedaws is

**Vedaws** is a **domain-neutral Development Operating System (DevOS)** — a **Python runtime** that orchestrates project state, workflows, workers, automation, and AI capabilities through a **plugin-first architecture**.

From `vedaws/README.md` and `vedaws/design/000_VISION.md`:

> Vedaws is a domain-neutral Development Operating System (DevOS) that orchestrates project state, workflows, workers, automation, and AI capabilities through a plugin-first architecture.

Tagline (`vedaws/design/000_VISION.md`): **"Orchestrate work. Not just code."**

Architecture version **0.5.0** frozen at Milestone 12 (`vedaws/design/README.md`, `vedaws/docs/ARCHITECTURE_FREEZE_V0.5.md`). Package installable via `pip install -e ".[dev]"` with `vedaws` CLI (`vedaws/VEDAWS_BOOTSTRAP.md`).

Ten core concepts (`vedaws/design/002_CORE.md`): Project, Runtime, Worker, Task, Workflow, State, Artifact, Plugin, Skill, Automation.

---

## 6. What problem Vedaws solves

Vedaws targets the **developer-as-implicit-runtime** anti-pattern (`vedaws/design/000_VISION.md`, `vedaws/design/001_PHILOSOPHY.md`):

Developers manually remember project state, decide the next step, coordinate AI tools, update documentation, and maintain workflow consistency. Vedaws aims to become **that runtime explicitly**.

Concrete capabilities shipped through Milestone 16 (`vedaws/VEDAWS_BOOTSTRAP.md`):

- `.vedaws/` project state, workflows, task dispatch
- Plugin platform with discovery and lifecycle
- Event bus and automation engine (`on_event` → `if` → `then`)
- AI provider SDK with capability-based routing
- First-party plugins: `git`, `software`, `unity`, `mock-ai`

---

## 7. Strengths of Vedaws

1. **Executable orchestration** — `vedaws run`, `vedaws workflow activate`, `vedaws status` (`vedaws/VEDAWS_BOOTSTRAP.md`).
2. **Formal project state machine** — 11 canonical states with valid transitions (`vedaws/design/006_STATE_MACHINE.md`).
3. **Workflow engine with dependencies** — TOML-defined tasks, `depends_on`, capability matching (`vedaws/plugins/software/templates/project/workflows/software.workflow.toml`, `vedaws/design/004_WORKERS.md`).
4. **Worker model** — Uniform execution boundary for AI, tools, scripts, humans (`vedaws/design/004_WORKERS.md`).
5. **Plugin platform maturity** — Ten contribution types: workers, commands, templates, skills, health checks, events, automation, AI providers, etc. (`vedaws/design/010_PLUGINS.md`).
6. **Domain-neutral core** — Software and Unity validated as separate plugins; no domain logic in `runtime/vedaws/` (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md` §Biggest successes).
7. **Automation engine** — Event-driven rules without hardcoded domain hooks (`vedaws/design/005_AUTOMATION.md`).
8. **AI capability routing** — Requests `implement`, `plan`, etc., not vendor names (`vedaws/design/017_AI_PROVIDERS.md`).
9. **Design-first discipline** — `design/` index matches implementation (`vedaws/design/README.md`).
10. **Integration tests** — 107 tests at v0.5 review; 121 cited in bootstrap (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md`, `vedaws/VEDAWS_BOOTSTRAP.md`).
11. **Operational CLI** — `vedaws doctor`, `vedaws init --template`, artifact checks (`vedaws/VEDAWS_BOOTSTRAP.md`, `vedaws/plugins/software/software_plugin/artifacts.py`).
12. **Explicit philosophy and anti-goals** — Documented boundaries against becoming an IDE, chatbot, or developer replacement (`vedaws/design/001_PHILOSOPHY.md`).

---

## 8. Weaknesses of Vedaws

From `vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md`, `vedaws/docs/ARCHITECTURE_FREEZE_V0.5.md`, and `vedaws/design/015_ROADMAP.md`:

1. **Not v1 production-ready** — v1 production readiness scored **5.5 / 10** at review (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md`).
2. **Memory system deferred** — No memory APIs; only file-backed state (`vedaws/design/009_MEMORY.md`).
3. **Synchronous orchestration ceiling** — In-process event bus; not suited for long AI latency or parallel teams at scale (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md` §Biggest risks).
4. **Security gaps** — Trust-all local plugins; no sandbox; permission declarations without enforcement (`vedaws/design/013_SECURITY.md`).
5. **No IDE/school submission workflow** — No equivalent to POS documenter pipeline, rubric-phased reports, or `HANDOFF_FOR_DOCUMENTER.md` automation.
6. **No UI design artifact contract** — Software plugin scaffolds `docs/` but not a `design/` screen-spec gate like PAWS.
7. **Version/documentation drift** — Package `0.1.0` vs design `0.5.0` at review time (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md`).
8. **Dual state sources** — `project.toml` mirrors `state.toml`; drift risk (`vedaws/design/007_PROJECT_MODEL.md`, architecture review).
9. **String-based cross-plugin coupling** — Automation references workers by id (e.g. `git.status`) without manifest-level trust boundaries (`vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md`).
10. **Heavy adoption cost** — Requires Python 3.11+, install, `.vedaws/` literacy (`vedaws/VEDAWS_BOOTSTRAP.md`).
11. **Deferred surfaces** — Distributed execution, MCP in core, scheduling, remote plugin registry, streaming UI (`vedaws/design/015_ROADMAP.md` §Explicitly deferred).
12. **Placeholder AI workers** — Worker manifests like `vedaws/workers/ai/claude/vedaws.worker.toml` describe capabilities; vendor integration is plugin-local, not turnkey in core.

---

## 9. Overlapping concepts

| Concept | PAWS expression | Vedaws expression |
|---------|-----------------|-------------------|
| **Project coordination** | POS layers; `tasks/current_task.md` | `Project` + `Runtime` (`vedaws/design/002_CORE.md`) |
| **Phased work** | CURRENT TASK + BACKLOG in Master Prompt | Workflow tasks with `depends_on` (`software.workflow.toml`) |
| **Project memory / docs** | `docs/architecture.md`, `api_contracts.md`, `decisions.md` | Software plugin scaffold: `docs/architecture/`, `docs/api/`, `docs/decisions/` (`vedaws/design/008_ARTIFACTS.md`) |
| **Handoff package** | `docs/HANDOFF_FOR_DOCUMENTER.md` | `docs/handoff/HANDOFF.md` in software template (`vedaws/plugins/software/.../HANDOFF.md`) |
| **Human authority** | Planner decides phases; executor implements; human tests | `awaiting_approval` state; philosophy: humans retain judgment (`vedaws/design/006_STATE_MACHINE.md`, `001_PHILOSOPHY.md`) |
| **Planner vs executor split** | Explicit in POS roles | Runtime coordinates; workers execute (`vedaws/design/001_PHILOSOPHY.md`) |
| **Domain neutrality** | Tool-neutral toolchain docs | Core runtime domain-neutral; plugins for software/Unity (`vedaws/design/000_VISION.md`) |
| **Explicit state** | `tasks/status.md`, task Status field | `state.toml` + `transitions.jsonl` (`vedaws/design/007_PROJECT_MODEL.md`) |
| **Architecture decisions** | `docs/decisions.md` ADR template | `docs/decisions/DECISIONS.md` in software scaffold |
| **Reduce developer coordination load** | Lazy workflow, auto HANDOFF | Vision/philosophy: replace implicit runtime (`vedaws/design/000_VISION.md`) |
| **Software lifecycle phases** | Planner backlog phases (scope, implement, test, etc.) | Software workflow: scope → architecture → api-design → implement → test → review → handoff (`software.workflow.toml`) |
| **Skills / know-how** | Agent prompts in `.ai/` | `Skill` concept + `software.*` skills (`vedaws/design/011_SKILLS.md`) |

---

## 10. Concepts unique to PAWS

| Concept | Evidence |
|---------|----------|
| **POS MASTER PROMPT** intake format | `paws022/.ai/planner_prompt.md` |
| **Kernel / Memory / Scheduler / Userspace** layer model | `paws022/.ai/system_prompt.md`, `executor_rules.md` |
| **External agent prompt library** (planner, documenter, UI designer, follow-up messages) | `paws022/.ai/planner_prompt.md`, `documenter_prompt.md`, `ui_designer_prompt.md`, `*_followup_message.md` |
| **`design/` UI artifact contract** (DESIGN.md, sources.md, screens/, exports/) | `paws022/design/README.md`, `docs/UI_DESIGN.md` |
| **Design-before-code gate** for new screens | `paws022/design/DESIGN.md` Implementation gate |
| **Submission documentation pipeline** (rubric-phased school reports) | `paws022/docs/SUBMISSION_DOCUMENTATION.md` |
| **Sidecar layout** (`paws022/` + `main/`) | `paws022/docs/PROJECT_LAYOUT.md` |
| **Adopt bootstrap** for existing repos without moving code | `paws022/docs/ADOPT_EXISTING_PROJECT.md`, `ADOPT_BOOTSTRAP_PROMPT.md` |
| **HANDOFF executor auto-maintenance** | `paws022/.ai/executor_rules.md` §Handoff automation |
| **Tool-neutral multi-IDE rules** (no Python runtime) | `paws022/docs/TOOLCHAIN.md`, `AGENTS.md` |
| **Optional Stitch/MCP UI workflow** (executor-side) | `paws022/docs/STITCH_CURSOR.md`, `UI_DESIGN.md` |
| **`tasks/intake.md`** raw dump before planning | `paws022/tasks/intake.md` |
| **instructionsVersion** template sync model | `paws022/docs/UPDATING.md` |

---

## 11. Concepts unique to Vedaws

| Concept | Evidence |
|---------|----------|
| **Python runtime + CLI** (`vedaws init`, `run`, `doctor`, …) | `vedaws/VEDAWS_BOOTSTRAP.md`, `runtime/vedaws/` |
| **`.vedaws/` project authority** on disk | `vedaws/design/007_PROJECT_MODEL.md` |
| **Canonical state machine** (11 states) | `vedaws/design/006_STATE_MACHINE.md` |
| **Workflow TOML** with task dependencies and capabilities | `vedaws/plugins/software/.../software.workflow.toml` |
| **Worker registry** + `TaskDispatch` / `TaskOutcome` contract | `vedaws/design/004_WORKERS.md` |
| **Worker manifests** (`vedaws.worker.toml`) | `vedaws/workers/ai/claude/vedaws.worker.toml`, worker tree |
| **Plugin platform** (`vedaws.plugin.toml`, lifecycle, SDK contributions) | `vedaws/design/010_PLUGINS.md` |
| **Event bus** (synchronous, in-process) | `vedaws/design/README.md` architecture layers |
| **Automation engine** (rules in `.vedaws/automation.toml`) | `vedaws/design/005_AUTOMATION.md` |
| **AI provider SDK** + capability routing in `config.toml` | `vedaws/design/017_AI_PROVIDERS.md` |
| **AI worker binding** (`AIExecutableWorker`) | `vedaws/design/018_AI_WORKERS.md` |
| **Skills as registered metadata** consumed at worker execution | `vedaws/design/011_SKILLS.md` |
| **Unity domain plugin** + game-dev artifact paths | `vedaws/design/008_ARTIFACTS.md` |
| **Git plugin** as tool integration pattern | `vedaws/design/010_PLUGINS.md`, `vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md` |
| **Architecture freeze + API stability contracts** | `vedaws/docs/ARCHITECTURE_FREEZE_V0.5.md`, `API_STABILITY.md` |
| **Architect escalation process** | `vedaws/.ai/architect_escalation.md` |
| **Deferred memory subsystem** (explicit non-implementation) | `vedaws/design/009_MEMORY.md` |

---

## 12. Which parts of Vedaws could improve PAWS

These are **observed gaps in PAWS** that Vedaws **already addresses** in its reference tree:

| Vedaws capability | How it could address a PAWS gap | Source |
|-------------------|----------------------------------|--------|
| **Executable `vedaws run` loop** | Replace manual "paste next Master Prompt" with deterministic task dispatch | `VEDAWS_BOOTSTRAP.md`, `004_WORKERS.md` |
| **State machine + `state.toml`** | Formal eligibility for what work can happen next | `006_STATE_MACHINE.md` |
| **Workflow dependencies** | Enforce scope → architecture → implement ordering | `software.workflow.toml` |
| **`vedaws doctor` health checks** | Detect misconfigured projects before coding | `VEDAWS_BOOTSTRAP.md`, `010_PLUGINS.md` |
| **Artifact presence CLI** (`vedaws software artifacts`) | Verify docs/handoff exist vs checklist only in markdown | `artifacts.py`, `008_ARTIFACTS.md` |
| **Automation rules** | Auto-trigger git status, state transitions on `TaskCompleted` | `005_AUTOMATION.md` |
| **Worker capability matching** | Route tasks to AI/tool/human workers by capability | `004_WORKERS.md`, `017_AI_PROVIDERS.md` |
| **Plugin extensibility** | Add domains (Unity, Git) without changing core template | `010_PLUGINS.md` |
| **Event bus integration** | Coordinate workflow, dispatch, plugins without ad-hoc scripts | `design/README.md` layers |
| **Skills metadata** | Structured execution guidance beyond free-text prompts | `011_SKILLS.md` |
| **Transition history** (`transitions.jsonl`) | Auditable state changes vs informal progress log | `007_PROJECT_MODEL.md` |

---

## 13. Which parts of PAWS should remain unchanged

These PAWS properties are **not replicated in Vedaws** and appear **intentionally valuable** for the use cases PAWS targets (especially coursework and IDE-first workflows):

| PAWS property | Why keep it | Source |
|---------------|-------------|--------|
| **Markdown-first, no runtime required** | Lowest barrier; works in any repo without Python install | `paws022/` contents; `TOOLCHAIN.md` |
| **POS MASTER PROMPT contract** | Proven structured handoff from planner to executor | `planner_prompt.md`, `executor_rules.md` |
| **Strict planner/executor/documenter role separation** | Prevents planning agents from coding; documenter last | `EXECUTOR_LOOP.md`, `documenter_prompt.md` |
| **`design/` UI spec + implementation gate** | Prevents executor from inventing screens ad hoc | `UI_DESIGN.md`, `design/DESIGN.md` |
| **HANDOFF_FOR_DOCUMENTER auto-maintenance** | Factual bridge to submission reports | `executor_rules.md`, `HANDOFF_FOR_DOCUMENTER.md` |
| **Phased rubric-aligned reporting** | Matches academic grading workflows | `SUBMISSION_DOCUMENTATION.md` |
| **Sidecar layout** (`paws022/` + `main/`) | Separates OS kernel from publishable app code | `PROJECT_LAYOUT.md` |
| **Tool-neutral external agent setup** | Users choose Gemini, ChatGPT, Cursor, etc. | `EXTERNAL_AGENTS_SETUP.md` |
| **Adopt-existing-project without moving `src/`** | Wrap legacy codebases | `ADOPT_EXISTING_PROJECT.md` |
| **Kernel vs memory split** | Template updates without overwriting product facts | `.ai/README.md`, `system_prompt.md` |
| **Minimal-diff executor discipline** | Focused changes per task | `coding_rules.md`, `executor_rules.md` |
| **Debugging protocol** | Consistent defect investigation across projects | `debugging_protocol.md` |
| **MySQL-as-default planner hint** | Aligns with stated user preference in POS planner (when DB is used) | `planner_prompt.md` |

---

## 14. Questions that must be answered before designing Vespawd

Derived from **tensions and gaps visible in both trees only**:

### Product scope

1. Is Vespawd primarily a **coursework/creator OS** (PAWS lineage), a **DevOS runtime** (Vedaws lineage), or a **deliberate merge**? Neither repo defines "Vespawd" yet (`paws022/.ai/project_context.md` names "vespawd" but fields are `_TBD_`).

2. Must Vespawd work **without installing Python**, or is a runtime dependency acceptable?

3. Should the **sidecar layout** (`paws022/` + `main/`) remain the canonical Vespawd workspace shape (`PROJECT_LAYOUT.md`)?

### Orchestration model

4. Will task progression be **file-convention enforced** (PAWS), **runtime enforced** (Vedaws), or **hybrid**?

5. If hybrid: does POS MASTER PROMPT remain the planner→executor contract, or does Vedaws workflow TOML supersede it?

6. What is the **authoritative state** — `tasks/current_task.md`, `.vedaws/state.toml`, both synced, or one subordinate to the other?

### Roles and agents

7. Are **planner / executor / documenter / UI designer** still distinct roles, or collapsed into Vedaws workers?

8. Where do **external agent prompts** live — PAWS `.ai/` copies, Vedaws skills, plugin contributions, or a new location under `main/`?

9. Is the **documenter + rubric + HANDOFF** pipeline a first-class Vespawd requirement?

### UI and artifacts

10. Does Vespawd adopt PAWS **`design/` gate** alongside Vedaws **software artifact paths** (`docs/architecture/`, etc.)?

11. How are **UI tools** (Stitch MCP, Figma exports) integrated if orchestration moves toward Vedaws CLI?

### Domain and extensibility

12. Which Vedaws **plugins** are in scope for Vespawd v1 — `software` only, or also `git`, `unity`, `mock-ai`?

13. Will Vespawd add a **POS plugin** (or equivalent) to Vedaws, or keep POS markdown kernel outside the runtime?

### Memory and persistence

14. Vedaws **memory is deferred** (`009_MEMORY.md`). Does Vespawd accept file-backed docs/tasks only, or block on memory design?

15. How does **project context** (`project_context.md`) relate to `.vedaws/project.toml` and `config.toml`?

### Operations and trust

16. What **security model** applies if Vedaws runtime loads plugins locally (`013_SECURITY.md` trust-all model)?

17. Is **synchronous orchestration** sufficient for Vespawd's expected AI latency and team size (`ARCHITECTURE_REVIEW_V0.5.md`)?

### Delivery and publishing

18. In sidecar mode, **git init defaults to app folder** — not `paws022/` (`PROJECT_LAYOUT.md`). Does Vespawd follow the same rule for `vedaws/` vs `main/`?

19. What is the **update/sync story** when POS `instructionsVersion` and Vedaws architecture version both change?

### Verification

20. What **health checks** define a "ready" Vespawd project — `vedaws doctor`, HANDOFF freshness, design gate status, tests?

21. What **test strategy** applies to Vespawd itself — Vedaws-style integration tests only, or also POS-style agent compliance checks (no automated tests exist in `paws022/`)?

---

## Summary table

| Dimension | PAWS (`paws022/`) | Vedaws (`vedaws/`) |
|-----------|-------------------|---------------------|
| **Nature** | Markdown template + agent prompts | Python DevOS runtime + CLI |
| **Orchestration** | Human + IDE agents follow files | Runtime: state, workflow, dispatch, automation |
| **Primary user** | Students/small teams with external planners | Developers orchestrating multi-step dev work |
| **State** | Informal task/backlog files | Formal state machine + TOML/JSONL |
| **Extensibility** | Copy/sync template kernel | Plugin platform |
| **UI workflow** | `design/` contract | Not defined in core |
| **Submission docs** | Documenter + HANDOFF + rubric | Handoff artifact in software plugin only |
| **Maturity in this workspace** | Docs-only frozen copy | Runnable, tested runtime |

---

## File index (key citations)

### PAWS

- `paws022/AGENTS.md` — POS entrypoint for agents
- `paws022/.ai/executor_rules.md` — Executor behavior, Master Prompt intake, HANDOFF
- `paws022/.ai/planner_prompt.md` — Planner output contract
- `paws022/.ai/system_prompt.md` — Layer model
- `paws022/docs/LAZY_WORKFLOW.md` — End-to-end pipeline
- `paws022/docs/PROJECT_LAYOUT.md` — Integrated vs sidecar
- `paws022/docs/UI_DESIGN.md` — UI artifact contract
- `paws022/docs/SUBMISSION_DOCUMENTATION.md` — Academic reporting flow
- `paws022/docs/TOOLCHAIN.md` — Role definitions

### Vedaws

- `vedaws/README.md`, `vedaws/VEDAWS_BOOTSTRAP.md` — Product summary and CLI
- `vedaws/design/000_VISION.md`, `001_PHILOSOPHY.md`, `002_CORE.md` — Vision and concepts
- `vedaws/design/006_STATE_MACHINE.md`, `007_PROJECT_MODEL.md` — State and on-disk layout
- `vedaws/design/004_WORKERS.md`, `005_AUTOMATION.md`, `010_PLUGINS.md` — Execution and extension
- `vedaws/design/008_ARTIFACTS.md`, `011_SKILLS.md`, `009_MEMORY.md` — Artifacts, skills, memory deferral
- `vedaws/docs/ARCHITECTURE_REVIEW_V0.5.md` — Strengths, weaknesses, risks
- `vedaws/plugins/software/templates/project/workflows/software.workflow.toml` — Software lifecycle workflow

---

*Generated for Vespawd early design. No code changes. Sources: `paws022/`, `vedaws/` only.*
