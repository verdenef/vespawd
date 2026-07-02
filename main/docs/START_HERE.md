# Start Here — Using Vespawd

**Vespawd is PAWS 2.0, powered by Vedaws.**

You do not need to learn Vedaws. You do not need to learn how PAWS was built. You talk to a **Planner**, paste a **POS MASTER PROMPT** into your **IDE** (the executor), test your app, and repeat until you are done.

Vedaws runs in the background and handles the bookkeeping PAWS used to leave to you — phase order, status sync, health checks, and artifact checklists. Your daily experience is still **chat-first development**.

For technical detail, see [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md).

---

## What you are doing (in one sentence)

You turn an assignment into working software by looping: **Planner → paste into your IDE → test → Planner again**.

---

## The four roles

| Role | Where | What it does | What it never does |
|------|-------|--------------|-------------------|
| **You** | Everywhere | Provide the assignment, test the app, approve each phase | Write long plans or reports by hand (unless you want to) |
| **Planner** | External chat (Gemini, ChatGPT, Claude, …) | Turns your assignment into a **POS MASTER PROMPT** | Write code |
| **Executor** | Your IDE (Cursor, VS Code, Windsurf, JetBrains AI, …) | Executes the Master Prompt: updates project files and writes code in `main/src/` | Replace the Planner for phase planning |
| **Documenter** | External chat (last step) | Writes your submission report from facts the executor collected | Invent features not in the handoff |

Optional: a **UI designer** (external chat) fills `paws022/design/DESIGN.md` before the executor builds screens.

---

## Your workspace (what the folders mean)

Open the **workspace root** in your IDE (the folder that contains `paws022/`, `vedaws/`, and `main/`).

```
vespawd/                 ← open THIS in your IDE
├── paws022/             ← project brain (tasks, docs, design, agent rules)
├── vedaws/              ← orchestration engine (installed once; you rarely touch it)
└── main/                ← your application code lives here
    ├── src/             ← the app you are building
    ├── docs/            ← technical docs for your app
    └── .vedaws/         ← auto-maintained; do not edit by hand
```

**Rule of thumb:** read tasks and docs in `paws022/`. Write application code in `main/src/`.

---

## One-time setup

Do this once per machine before your first project.

### 1. Install the orchestration engine

Vespawd needs Python 3.11+ and a one-time install of Vedaws from the `vedaws/` folder in this workspace:

```bash
cd vedaws
pip install -e ".[dev]"
vedaws version
```

You will not use Vedaws every day. The executor and the bridge invoke it when needed.

### 2. Set up your Planner (external)

Copy the planner instructions from `paws022/.ai/` into your chosen tool:

| Tool | What to copy |
|------|--------------|
| ChatGPT / Claude | Entire `paws022/.ai/planner_prompt.md` into Instructions |
| Gemini Gem | `planner_prompt_gem_instructions.txt` into Instructions **and** `planner_prompt_full.txt` into Knowledge |

Full setup notes: `paws022/docs/EXTERNAL_AGENTS_SETUP.md`.

The Planner must output a document that **starts with** `# POS MASTER PROMPT`. Nothing else before that line.

### 3. Set up your Documenter (external) — do this before you finish

Copy `paws022/.ai/documenter_prompt.md` into a second external chat. You will use it at the **end** of the project, not during build.

### 4. Open your IDE on the workspace root

Enable PAWS executor rules in your IDE:

| IDE | What to enable |
|-----|----------------|
| **Cursor** | `paws022/.cursor/rules/pos.mdc` (automatic) + `main/.cursor/rules/vespawd.mdc` when present |
| **VS Code, Windsurf, JetBrains, other** | `paws022/AGENTS.md` and paste `paws022/.ai/executor_rules.md` into project instructions |

See `paws022/docs/TOOLCHAIN.md` for other stacks.

---

## Creating a new project

### Step 1 — Bootstrap the app folder

From the workspace root, initialize orchestration in `main/` (one time per project):

```bash
cd main
vedaws init --template software --name my-project
```

The executor can also trigger this on your first Master Prompt if you prefer chat-only setup. Either way, you should end up with a `main/.vedaws/` folder. **Do not edit files inside `.vedaws/` manually.**

### Step 2 — Dump your assignment

Paste your assignment, rubric, and rough ideas into:

`paws022/tasks/intake.md`

No special format. This is raw input for you and the Planner.

### Step 3 — Tell the Planner

Open your Planner chat. Send:

- The contents of `paws022/tasks/intake.md`
- Any deadlines, rubric, or stack preferences (e.g. MySQL)
- For phase 1: “This is a new project. Output Phase 1 only in CURRENT TASK; put later phases in BACKLOG.”

The Planner replies with a **POS MASTER PROMPT**.

---

## Where project knowledge lives

Everything important is written to files so you and the executor never rely on chat memory alone.

| What | Where | Who maintains it |
|------|-------|------------------|
| Product name, stack, constraints | `paws022/.ai/project_context.md` | Executor (from Master Prompt) |
| What you are doing **right now** | `paws022/tasks/current_task.md` | Executor + bridge sync |
| Future phases | `paws022/tasks/backlog.md` | Executor (from Master Prompt) |
| Phase snapshot | `paws022/tasks/status.md` | Auto-synced (was manual in PAWS 1) |
| Architecture | `paws022/docs/architecture.md` | Executor |
| API contracts | `paws022/docs/api_contracts.md` | Executor |
| Database schema | `paws022/docs/db_schema.md` | Executor |
| Decisions (ADRs) | `paws022/docs/decisions.md` | Executor |
| UI spec (if applicable) | `paws022/design/DESIGN.md` | UI designer or executor |
| Submission facts | `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` | Executor (automatically) |
| Finished work log | `paws022/tasks/completed/` | Executor |
| **Your application code** | `main/src/` | Executor |
| Orchestration state (invisible) | `main/.vedaws/` | Bridge + Vedaws (automatic) |

**Where to look when you are lost:** open `paws022/tasks/current_task.md`. That is always “what am I doing now?”

---

## Where the Master Prompt comes from

The **POS MASTER PROMPT** is always produced by your **Planner** — never by the executor, never by you typing it from scratch.

It is a structured markdown document with these sections (in this order):

1. `# POS MASTER PROMPT`
2. `## PROJECT BRIEF`
3. `## PROJECT CONTEXT UPDATES`
4. `## CURRENT TASK` (with Goal, Constraints, Acceptance criteria)
5. `## BACKLOG ITEMS`
6. `## EXECUTOR INSTRUCTIONS`

The Planner writes **planning only**. Phase 1 goes in CURRENT TASK; later phases go in BACKLOG. School report / submission documentation belongs **last** in BACKLOG.

Format reference: `paws022/.ai/planner_prompt.md`.

---

## The main loop: Planner → IDE → test → Planner

This is the heart of Vespawd. You will repeat it many times.

```
┌─────────────┐
│  Assignment │
└──────┬──────┘
       ▼
┌─────────────┐     POS MASTER PROMPT      ┌─────────────┐
│   Planner   │ ─────────────────────────► │  Executor   │
│  (external) │                            │   (IDE)     │
└─────────────┘                            └──────┬──────┘
       ▲                                            │
       │                                            ▼
       │                                     You test the app
       │                                            │
       │         ┌──────────────────────────────────┘
       │         │
       │    Small fix? ──► stay in IDE chat
       │    Next phase? ──► Planner follow-up (below)
       └─────────┘
```

### Execute a Master Prompt in your IDE

1. Copy the entire Planner output (starting with `# POS MASTER PROMPT`).
2. Open your IDE’s agent chat.
3. Send:

   ```text
   Execute this.
   ```

   Then paste the Master Prompt.

4. Let the executor work. It will update project files and implement in `main/src/`.

You do **not** need to manually edit `paws022/tasks/current_task.md` first. The executor does that for you.

### After the executor finishes — you test

Run your app. Click through it. Run tests. Note what works and what does not.

| Result | What to do next |
|--------|-----------------|
| **Small bug or tweak** | Stay in your IDE. Describe the fix in agent chat. |
| **Phase acceptance criteria met** | Go to Planner for the **next phase** (below). |
| **Something is blocked** | See [When things get stuck](#when-things-get-stuck). |

### Start the next phase (Planner follow-up)

When a phase is done and tested, open your Planner again.

Use the template in `paws022/.ai/planner_followup_message.md`. Fill in:

- What was completed since the last Master Prompt
- What runs / what does not
- Problems
- The **next goal only** (one phase per Master Prompt)

The Planner outputs a **new** POS MASTER PROMPT. Paste it into your IDE with `Execute this.` again.

Repeat until BACKLOG is empty and the app is feature-complete.

---

## The full journey: beginning to end

### Phase 0 — Setup (once)

- Install Vedaws (`pip install -e` in `vedaws/`)
- Configure Planner and Documenter external chats
- `vedaws init --template software` in `main/`
- Paste assignment into `paws022/tasks/intake.md`

### Phase 1 — First Master Prompt

- Planner → POS MASTER PROMPT (Phase 1 only)
- Executor → `Execute this.` + paste
- You test

Typical first-phase goals: project scope, initial architecture, or a thin vertical slice.

### Phases 2 … N — The loop

For each backlog item the Planner assigned:

1. Planner follow-up → new Master Prompt
2. Executor → execute
3. You test
4. Repeat

Vespawd aligns phases with a standard software lifecycle behind the scenes (scope → architecture → API design → implement → test → review → handoff). You still think in **Planner phases**; you do not need to name these steps yourself.

### UI-heavy projects (optional branch)

If your app has real screens:

1. Planner puts a UI phase in BACKLOG
2. Optional: UI designer → updates `paws022/design/DESIGN.md`
3. Executor reads `design/DESIGN.md` before building UI in `main/src/`

Until `design/DESIGN.md` is ready (or you say **skip design** in IDE chat), the executor should not invent major new screens. Details: `paws022/docs/UI_DESIGN.md`.

### Final phase — Handoff

When implementation is done, the Planner’s BACKLOG should include a **handoff** item. The executor refreshes:

`paws022/docs/HANDOFF_FOR_DOCUMENTER.md`

This file is **facts only** — what was built, how to run it, stack, features, limitations. No essay prose.

The executor will tell you when submission handoff is ready for your documenter and rubric.

Optional check before submitting:

```bash
vedaws software artifacts --path main
```

This confirms required documentation files exist.

### Last step — Documenter (submission report)

1. Open your Documenter chat.
2. Paste the latest `paws022/docs/HANDOFF_FOR_DOCUMENTER.md`.
3. Paste your rubric / assignment format.
4. Write **one section at a time** (recommended). Use `paws022/.ai/documenter_followup_message.md` between sections.

Details: `paws022/docs/SUBMISSION_DOCUMENTATION.md`.

You are finished when your report is submitted and you accept the project as complete.

---

## What the executor updates automatically

When you paste a Master Prompt, the executor (your IDE agent) is responsible for:

| Action | File(s) |
|--------|---------|
| Set the active task | `paws022/tasks/current_task.md` |
| Merge product facts | `paws022/.ai/project_context.md` |
| Append future work | `paws022/tasks/backlog.md` |
| Seed / refresh submission facts | `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` |
| Update phase snapshot | `paws022/tasks/status.md` |
| Update architecture / API / schema when boundaries change | `paws022/docs/*.md` |
| Write application code | `main/src/` |
| Log completed phases | `paws022/tasks/completed/` |
| Trigger bridge sync | `main/.vedaws/` (orchestration — you do not edit this) |

You should not need to maintain two copies of “what phase am I on?” The executor and the bridge keep `current_task.md` and orchestration state aligned.

---

## What you are responsible for

| You do | You do not do |
|--------|---------------|
| Provide the assignment and rubric | Write POS MASTER PROMPTs by hand |
| Configure Planner and Documenter once | Manually edit `tasks/current_task.md` on every phase |
| Paste Master Prompt into your IDE | Edit `main/.vedaws/` by hand |
| **Test the app after each phase** | Commit to git unless you choose to |
| Decide when a phase is “good enough” to advance | Write the submission report during build |
| Run Planner follow-up for the next phase | Learn Vedaws internals |
| Paste HANDOFF + rubric into Documenter at the end | |

**The human gate is intentional.** The executor implements; **you** verify. Vespawd waits for your approval between Planner phases (`paws022/docs/EXECUTOR_LOOP.md`).

---

## What Vedaws automates behind the scenes

You do not interact with Vedaws during normal work. The **bridge** in `main/` calls it when the executor finishes key steps.

| PAWS 1 (manual) | Vespawd (automatic via Vedaws) |
|-----------------|--------------------------------|
| Easy to forget phase order | Enforces workflow dependencies (scope before implement, etc.) |
| `tasks/status.md` often stale | Syncs status from orchestration state |
| No health check before moving on | Runs `vedaws doctor` when blocked or at handoff |
| Manual “are all docs present?” | Can verify artifacts (`vedaws software artifacts`) |
| You remember what step is next | Projects the active workflow task into `current_task.md` |
| Git status after implement is manual | Can auto-run git checks via automation rules |

**Hidden from you (on purpose):** state machines, event buses, worker dispatch, plugin lifecycles, and TOML workflow files. They live under `main/.vedaws/` and `vedaws/`. The executor and the bridge use them; you read markdown in `paws022/`.

---

## When things get stuck

The executor may report a blocker — design gate not met, doctor failure, or phase out of order.

Run these **only when the executor or status tells you to**:

```bash
# Is the project healthy?
vedaws doctor --path main

# What phase is orchestration on?
vedaws status --path main

# Are documentation artifacts present?
vedaws software artifacts --path main
```

If `paws022/tasks/current_task.md` shows `Status: blocked`, fix the issue in IDE chat (or complete the missing design doc), then re-run the current phase.

For bugs in your app, stay in your IDE and follow `paws022/.ai/debugging_protocol.md`. Update `current_task.md` with what you tried if you are still stuck.

---

## Daily workflow

This is what a normal Vespawd day looks like after setup.

### Morning — orient

1. Open your IDE on the workspace root.
2. Read `paws022/tasks/current_task.md` — know today’s goal.
3. Glance at `paws022/tasks/status.md` — see phase and handoff freshness.

### Work session — one of two modes

**Mode A — Executing a planned phase**

1. Paste Master Prompt into your IDE: `Execute this.` + prompt.
2. Watch the executor update files and `main/src/`.
3. Run the app. Test acceptance criteria from `current_task.md`.
4. Small fixes → IDE chat. Phase done → Planner follow-up.

**Mode B — Between phases**

1. Open Planner.
2. Send follow-up from `paws022/.ai/planner_followup_message.md`.
3. Receive new POS MASTER PROMPT.
4. Switch to Mode A.

### End of day — optional checkpoint

- If you finished a phase: confirm `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` was refreshed.
- If the executor marked the task complete, `paws022/tasks/completed/` may have a new log entry.
- Commit `main/` to git if you use version control (only when you choose to).

### You never need to daily

- Run Vedaws commands (unless diagnosing a block)
- Edit `.vedaws/` files
- Re-copy planner instructions (unless the template updated)
- Manually sync backlog and orchestration

---

## Quick reference card

```
SETUP (once)     Planner instructions + vedaws init in main/
INTAKE           paws022/tasks/intake.md
PLAN             Planner → # POS MASTER PROMPT
BUILD            IDE     → Execute this. + paste
TEST             You run the app
LOOP             Planner follow-up → IDE → test → …
HANDOFF          Executor fills paws022/docs/HANDOFF_FOR_DOCUMENTER.md
REPORT           Documenter + HANDOFF + rubric (last)
CODE             main/src/
NOW              paws022/tasks/current_task.md
```

---

## Further reading

| Topic | Document |
|-------|----------|
| Architecture (technical) | [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) |
| PAWS vs Vedaws comparison | [PAWS_VS_VEDAWS_ANALYSIS.md](PAWS_VS_VEDAWS_ANALYSIS.md) |
| Planner setup | `paws022/docs/EXTERNAL_AGENTS_SETUP.md` |
| UI design flow | `paws022/docs/UI_DESIGN.md` |
| Submission reports | `paws022/docs/SUBMISSION_DOCUMENTATION.md` |
| Planner ↔ executor loop | `paws022/docs/EXECUTOR_LOOP.md` |

---

*Vespawd: PAWS 2.0 workflow. Vedaws orchestration. Your IDE builds. You decide when each phase is done.*
