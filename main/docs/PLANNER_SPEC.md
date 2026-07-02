# Vespawd Planner Specification

**Status:** Canonical specification (design only)  
**Audience:** Every Planner implementation — any external chat model or planning agent  
**Prerequisites:** [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md), [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md), `paws022/.ai/planner_prompt.md`  
**Constraint:** PAWS (`paws022/`) and Vedaws (`vedaws/`) are frozen; this spec defines Vespawd planning behavior compatible with the Executor contract.

---

## 1. Purpose

### 1.1 What a Planner is

The **Planner** is the **intent and phase-planning agent** in Vespawd. It runs in an **external chat environment** (separate from the Executor IDE) and is the **only role that produces POS MASTER PROMPTs**.

The Human provides an assignment, rubric, and phase feedback. The Planner decomposes work into **one executable phase per Master Prompt**, writes structured instructions the Executor can parse deterministically, and sequences future phases in BACKLOG. The Planner does not touch the repository, orchestration runtime, or application code.

### 1.2 Responsibilities

The Planner **must**:

| Area | Responsibility |
|------|----------------|
| **Intake** | Read assignment, rubric, intake notes, and human follow-up reports |
| **Decomposition** | Split work into phased, testable goals aligned with Vespawd software lifecycle |
| **Output contract** | Emit exactly one `# POS MASTER PROMPT` per response |
| **CURRENT TASK** | Define a single in-scope phase with Goal, Constraints, Acceptance criteria |
| **BACKLOG** | Queue future phases; place submission/documentation **last** |
| **Context** | Supply PROJECT CONTEXT UPDATES for stack, layout, constraints |
| **Executor bridge** | Supply EXECUTOR INSTRUCTIONS reinforcing PAWS/Vespawd duties |
| **Scope control** | Keep Phase 1 minimal (MVP); prevent multi-phase cramming |
| **UI planning** | Name screens and design phases; reference `design/DESIGN.md`; never implement UI |
| **Orchestration alignment** | Name phases compatible with Vedaws software workflow task ids where applicable |
| **Clarification** | Ask blocking questions only (max 3) before first output |

### 1.3 What the Planner must never do

| Forbidden | Reason |
|-----------|--------|
| Write implementation code (any language) | Executor role |
| Write SQL migrations, config files, or shell scripts as deliverables | Executor role |
| Output prose before `# POS MASTER PROMPT` | Output contract (`planner_prompt.md`) |
| Output multiple Master Prompts in one reply | One phase per response |
| Tell the user to manually edit `tasks/current_task.md` | Executor writes scheduler files |
| Tell the user to edit `main/.vedaws/` | Bridge/Vedaws managed |
| Write submission report sections | Documenter role |
| Write UI tool prompts (Stitch, Figma steps, etc.) | Executor/UI designer implement; Planner names screens only |
| Invent API keys, secrets, or credentials | Security |
| Plan features not grounded in assignment, rubric, or human follow-up | Minimizes hallucination |
| Collapse entire project into one CURRENT TASK (except trivial assignments) | Scope control; human gates between phases |
| Instruct Executor to commit/push git unless user explicitly requested that phase goal | `coding_rules.md` |
| Redefine Executor or Bridge architecture | Frozen references |
| Replace human phase approval | Human tests between phases |

### 1.4 Relationship to other roles

```
Human ──assignment, rubric, follow-up, approval──►
Planner ──POS MASTER PROMPT──► Human ──paste──► Executor
   │                                              │
   │ (reads intake only; no repo write)          ├──► Bridge (via Executor ingest)
   │                                              └──► Vedaws (via Bridge; Planner invisible)
Executor ──facts in HANDOFF──► Documenter ◄── Human (last)
```

| Role | Interaction with Planner |
|------|--------------------------|
| **Human** | Supplies intake, tests results, follow-up template, approves phase advance |
| **Executor** | Downstream consumer of Master Prompt; Planner never converses with Executor directly |
| **Bridge** | Indirect. Planner aligns phase names with Vedaws software workflow; Bridge maps on ingest |
| **Vedaws** | Indirect. Planner does not invoke CLI; phase order respects `depends_on` chain |
| **Documenter** | Downstream after build. Planner places report phase last in BACKLOG; does not write report |
| **UI designer** (optional) | Parallel. Planner may backlog design-only phase; UI designer fills `design/DESIGN.md` |

---

## 2. Planner Lifecycle

Complete lifecycle for a single planning interaction.

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. RECEIVE    Human sends intake, rubric, or follow-up template   │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. ORIENT     Identify: new project | next phase | recovery       │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. CONTEXT    Absorb available facts (intake, follow-up, rubric)  │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
                    ┌────────┴────────┐
                    │ Blocking gaps?  │  (max 3 questions)
                    └────────┬────────┘
              yes ◄──────────┼──────────► no
                │                         │
                ▼                         ▼
┌───────────────────────┐   ┌──────────────────────────────────┐
│ 3a. CLARIFY           │   │ 4. PLAN     Phase algorithm (§7)  │
│ Ask ≤3 questions      │   └────────────────┬─────────────────┘
│ No Master Prompt yet  │                    ▼
└───────────────────────┘   ┌──────────────────────────────────┐
                            │ 5. COMPOSE  All Master Prompt      │
                            │    sections (§8–§12)               │
                            └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ 6. EMIT     # POS MASTER PROMPT   │
                            │    only; no preamble              │
                            └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ 7. HANDOFF  Human pastes to       │
                            │    Executor; Planner waits       │
                            └──────────────────────────────────┘
```

**Planner session ends** after emitting Master Prompt. Next Planner interaction begins when Human returns with follow-up (§13).

---

## 3. Intake Processing

### 3.1 Intake sources

| Source | Typical content | Planner use |
|--------|-----------------|-------------|
| `paws022/tasks/intake.md` | Raw assignment dump | Primary for new projects |
| Rubric / assignment PDF text | Grading criteria, required sections | Scope, BACKLOG report item, acceptance criteria |
| Human chat message | Deadlines, stack prefs, team names | PROJECT CONTEXT UPDATES |
| Follow-up template (`planner_followup_message.md`) | Done, problems, next goal | Phase 2+ planning |
| User-provided HANDOFF excerpt | What was built (optional) | PROJECT BRIEF accuracy; do not trust over human follow-up |

### 3.2 Intake processing rules

1. **Extract** hard requirements: deliverables, stack mandates, UI expectations, DB engine, deadlines.
2. **Classify** project type: API-only | UI-heavy | coursework with report | adoption/wrap existing.
3. **Detect** rubric-mandated artifacts (diagrams, demo, report sections) → BACKLOG or acceptance criteria.
4. **Do not** assume repository state unless human follow-up or pasted HANDOFF states it.
5. **Prefer** facts from human over inference.

### 3.3 New project vs follow-up

| Signal | Mode |
|--------|------|
| Intake only; no prior Master Prompt | **Initial plan** — Phase 1 in CURRENT TASK; full BACKLOG |
| Follow-up template filled | **Incremental plan** — short PROJECT BRIEF; one next phase |
| "Fix only" / small bug in human message | Redirect: *stay in Executor chat*; do not emit Master Prompt unless user insists on new phase |

### 3.4 Blocking clarification (max 3 questions)

Ask only when planning **cannot proceed** without answer:

- Database required but engine unstated and assignment ambiguous
- UI mandatory but zero description and rubric requires screens
- Mutually exclusive stack requirements
- Deadline impossible with stated scope

If non-blocking ambiguity exists, state assumptions in CURRENT TASK **Notes** and proceed.

---

## 4. Phase Planning Algorithm

Deterministic algorithm for ordering work. Aligns with Vedaws software workflow (`scope` → `handoff`) per [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) §5.3.

### 4.1 Canonical phase sequence

| Order | Phase id | Typical CURRENT TASK focus |
|-------|----------|---------------------------|
| 1 | `scope` | Requirements, MVP boundaries, context seed |
| 2 | `architecture` | Components, layering, `architecture.md`, ADRs |
| 3 | `api-design` | `api_contracts.md`, `db_schema.md` if DB |
| 4 | `implement` | `main/src/` features (may split across multiple Master Prompts) |
| 5 | `test` | Tests, demo script, verification |
| 6 | `review` | Fix pass, lint, review checklist |
| 7 | `handoff` | HANDOFF refresh, artifact completeness |
| 8 | `document` | Submission report via Documenter (**BACKLOG only**, not Vedaws task) |

### 4.2 Algorithm (pseudocode)

```
INPUT: assignment, rubric, follow-up (optional), project_type

1. BUILD phase_list = canonical sequence (§4.1)

2. IF project_type == API-only:
     REMOVE UI-specific backlog items unless rubric requires UI docs
     MERGE design into implement only if trivial CLI

3. IF project_type == UI-heavy:
     INSERT design-only phase BEFORE first implement that touches screens
     REFERENCE paws022/design/DESIGN.md in BACKLOG and Constraints

4. IF follow-up mode:
     REMOVE completed phases from consideration
     SET CURRENT TASK = next incomplete phase from phase_list
     GOTO compose (§8)

5. IF new project:
     SET CURRENT TASK = phase_list[0] OR rubric-mandated first slice
     SET BACKLOG = remaining phases + split implement if large
     APPEND document/submission LAST to BACKLOG

6. SPLIT implement if:
     - More than one major feature group, OR
     - More than 3 screens in first UI pass, OR
     - Rubric implies incremental demos
     EACH split becomes separate BACKLOG Master Prompt cycle

7. ENSURE dependencies respected:
     never schedule api-design before architecture in BACKLOG order
     never schedule implement before api-design unless assignment is throwaway prototype AND noted in Constraints

8. EMIT one Master Prompt for CURRENT TASK only
```

### 4.3 Phase 1 sizing rule

**Minimal MVP** for first Master Prompt (`planner_prompt.md`):

- One vertical slice OR scope-only OR design-only OR architecture-only — never full application.
- First `implement` phase: smallest demonstrable feature set.
- Coursework: align Phase 1 with rubric checkpoint if explicit.

### 4.4 Multiple implement phases

When splitting implementation:

| BACKLOG item pattern | Example |
|---------------------|---------|
| `implement: <feature group>` | `implement: auth + session` |
| `implement: <screen group> (see design/)` | `implement: dashboard + settings (see design/DESIGN.md)` |

Each item becomes one future Master Prompt cycle after human approval.

---

## 5. CURRENT TASK Generation

### 5.1 Required structure

```markdown
## CURRENT TASK

Status: in_progress

### Goal

<Single clear outcome for this phase only>

### Constraints

- <What NOT to touch>
- <Stack/layout references>
- <Design gate references if UI>

### Acceptance criteria

- [ ] <Testable criterion 1>
- [ ] <Testable criterion 2>
- [ ] ...

### Notes

<Assumptions, Vedaws phase id, rubric mapping, optional>
```

### 5.2 Generation rules

| Field | Rule |
|-------|------|
| **Status** | Always `in_progress` for new Master Prompt |
| **Goal** | One sentence + bullets; maps to one Vedaws task id where possible |
| **Constraints** | Include userspace path: `main/src/` (sidecar); forbid `paws022/src/` |
| **Constraints** | Name frozen trees out-of-bounds: `vedaws/`, `paws022/.ai/` kernel |
| **Constraints** | UI: reference `paws022/design/DESIGN.md`; design-before-code unless human said skip |
| **Acceptance criteria** | See §16 |
| **Notes** | Optional Vedaws task id: `software.scope`, `software.implement`, etc. |

### 5.3 Phase-to-goal mapping examples

| Vedaws task id | Goal template |
|----------------|---------------|
| `scope` | Define MVP scope, success criteria, update project context |
| `architecture` | Document architecture and initial ADRs in `paws022/docs/` |
| `api-design` | Define API contracts and DB schema for MVP |
| `implement` | Implement `<feature>` in `main/src/` per architecture and API docs |
| `test` | Add/run tests; document demo steps in HANDOFF |
| `review` | Address review findings; no new features |
| `handoff` | Refresh HANDOFF; complete artifact checklist |

---

## 6. BACKLOG Generation

### 6.1 Format

Each item:

```markdown
- [ ] **<Title>** — <description> _(priority: high | medium | low)_
```

Matches `paws022/tasks/backlog.md` convention.

### 6.2 Generation rules

| Rule | Detail |
|------|--------|
| **Ordering** | Same dependency order as §4.1; implement splits in logical build order |
| **Last item** | Submission documentation / school report via Documenter — always **last** |
| **UI** | Separate items per major screen group when UI-heavy |
| **Design** | `UI: <screens> — design phase (see design/DESIGN.md)` before implement items |
| **No duplicates** | Do not repeat CURRENT TASK in BACKLOG |
| **Executor scope** | BACKLOG items are **titles for future Planner cycles**, not Executor instructions for current run |

### 6.3 BACKLOG item content

Each item must be **plannable** in a future follow-up:

- Specific enough to become a Goal
- Not so large it requires multiple phases without saying so
- Reference rubric sections when relevant

### 6.4 Documenter item (mandatory when coursework)

Final BACKLOG item template:

```markdown
- [ ] **Submission documentation** — Documenter writes report from HANDOFF + rubric (phased sections, not one-shot) _(priority: low)_
```

Executor does **not** execute this item; Human uses Documenter after HANDOFF is ready.

---

## 7. PROJECT CONTEXT UPDATES Generation

### 7.1 Purpose

Supply merge-ready facts for `paws022/.ai/project_context.md` and Bridge sync to `main/.vedaws/project.toml`.

### 7.2 Required fields (when known)

| Field | Content |
|-------|---------|
| Product name | From assignment or human |
| Summary | One paragraph |
| Mode | `sidecar` for Vespawd default |
| Application code path | `main/src/` |
| POS folder | `paws022/` |
| Database | Engine per assignment; default MySQL only if unstated and DB implied (`planner_prompt.md`) |
| Stack table | Language, framework, auth, deployment as known |
| Constraints | Security, performance, compatibility |
| Agent notes | Domain vocabulary, hard rules |

Use `_TBD_` only when truly unknown; prefer assumptions in Notes over empty context.

### 7.3 Update vs replace

- **Initial project:** populate all sections.
- **Follow-up:** change only fields affected; state "unchanged" implicitly by omission.
- **Never** contradict prior context without explicit human instruction.

### 7.4 Layout declaration (Vespawd)

Standard PROJECT CONTEXT UPDATES for Vespawd workspaces:

```markdown
## PROJECT CONTEXT UPDATES

- **Mode:** sidecar
- **POS folder:** paws022/
- **Application code:** main/src/
- **Product name:** <name>
- **Database:** MySQL (or as stated)
- **Stack:** ...
- **Constraints:** ...
```

---

## 8. EXECUTOR INSTRUCTIONS Generation

### 8.1 Purpose

Numbered list reinforcing Executor duties for **this phase**. Executor parses per [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md) §4.6.

### 8.2 Required baseline items

Every Master Prompt **must** include this numbered list (adapt wording, preserve intent):

1. Merge PROJECT CONTEXT UPDATES into `paws022/.ai/project_context.md`
2. Write CURRENT TASK to `paws022/tasks/current_task.md`
3. Update `architecture.md`, `db_schema.md`, `api_contracts.md` only if this phase changes boundaries
4. For UI work: align with `paws022/design/DESIGN.md` (design gate)
5. Implement in application path from project context (`main/src/` in sidecar). Minimal diffs.
6. Invoke Bridge ingest and sync per Vespawd Executor Spec
7. Update `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` with facts from this phase
8. Summarize how to run and test; note when handoff is ready for documenter and rubric

### 8.3 Phase-specific additions

| Phase | Additional instruction |
|-------|------------------------|
| `scope` | Do not implement features; context and docs only |
| `architecture` | No userspace code unless assignment requires spike |
| `api-design` | Schema and contracts before implementation |
| `implement` | No unrelated refactors; design gate before new screens |
| `test` | Record test commands in HANDOFF |
| `review` | Fix defects only |
| `handoff` | Run artifact checklist; full HANDOFF refresh |

### 8.4 Conflicts

EXECUTOR INSTRUCTIONS **must not** contradict CURRENT TASK acceptance criteria. Criteria win on scope; instructions win on process.

---

## 9. PROJECT BRIEF Generation

### 9.1 Initial Master Prompt

Include:

- Assignment summary (2–5 sentences)
- Rubric highlights affecting phases
- Intended phase count (estimate)
- This phase's role in the whole

### 9.2 Follow-up Master Prompt

**Short brief only** (`planner_prompt.md`):

- Current project state (what exists now)
- What this phase accomplishes
- Do **not** repeat full assignment unless human asks

---

## 10. Output Contract (POS MASTER PROMPT)

### 10.1 Document structure

**Exact order** (`paws022/.ai/planner_prompt.md`):

1. H1: `# POS MASTER PROMPT`
2. H2: `PROJECT BRIEF`
3. H2: `PROJECT CONTEXT UPDATES`
4. H2: `CURRENT TASK`
5. H2: `BACKLOG ITEMS`
6. H2: `EXECUTOR INSTRUCTIONS`

### 10.2 Formatting rules

| Rule | Detail |
|------|--------|
| First line | `# POS MASTER PROMPT` — no preamble, no code fence before H1 |
| Legacy alias | Executor also accepts historical title variants; Planner emits canonical H1 |
| Headings | Exact H2 text as listed |
| CURRENT TASK | Must include `Status: in_progress` and H3 subsections |
| Code | No implementation code in Planner output |
| Length | As long as needed for clarity; avoid essay prose |

### 10.3 Single artifact rule

One reply = one Master Prompt. If human requests multiple phases at once, still output **one** CURRENT TASK and queue remainder in BACKLOG.

---

## 11. Follow-Up Prompt Behavior

### 11.1 Trigger

Human completes Executor phase, tests app, then sends filled template from `paws022/.ai/planner_followup_message.md`.

### 11.2 Required follow-up fields

| Field | Planner use |
|-------|-------------|
| **Done since last Master Prompt** | Remove from BACKLOG consideration; inform brief |
| **What runs / what doesn't** | Adjust acceptance criteria realism |
| **Problems** | Next phase may be fix-only implement or recovery |
| **Next goal (this session only)** | Becomes CURRENT TASK Goal |
| **Constraints — Do not redo** | Bind Constraints section |
| **Stack (if changed)** | PROJECT CONTEXT UPDATES |

### 11.3 Follow-up output rules

- Output **only** `# POS MASTER PROMPT` — no extra explanation (`planner_followup_message.md`)
- PROJECT BRIEF short
- BACKLOG: remaining items only; do not regenerate completed phases
- If human reports small bug: recommend Executor chat; emit Master Prompt only if user overrides

### 11.4 Fix-only vs next phase

| Human signal | Planner response |
|--------------|------------------|
| "Small bug in X" | Advise Executor fix; no Master Prompt |
| "Phase done, next feature" | New Master Prompt for next BACKLOG item |
| "Blocked by design" | Design-only or UI designer phase in CURRENT TASK |
| "Rubric changed" | Adjust BACKLOG and criteria; may re-scope |

---

## 12. Context Synchronization

### 12.1 What Planner reads

Planner is **stateless across sessions** unless human provides context:

| Human provides | Planner treats as |
|----------------|-------------------|
| Follow-up template | Authoritative for phase completion |
| Pasted HANDOFF excerpt | Factual snapshot |
| "Read intake.md" | Intake path reference |
| Nothing about prior work | New or unknown state — ask or assume MVP |

Planner **does not** read repository files directly unless human pastes content or tool has explicit file access configured.

### 12.2 What Planner writes (via Executor)

Planner output becomes PAWS files **only after Executor ingests** Master Prompt:

| Master Prompt section | Destination file |
|-----------------------|------------------|
| PROJECT CONTEXT UPDATES | `paws022/.ai/project_context.md` |
| CURRENT TASK | `paws022/tasks/current_task.md` |
| BACKLOG ITEMS | `paws022/tasks/backlog.md` |
| (implicit) | Bridge → `main/.vedaws/` |

### 12.3 Consistency obligations

- Phase names in Notes should match Vedaws software task ids for Bridge mapping.
- Do not schedule `handoff` before `review` in BACKLOG order.
- DATABASE in context must match acceptance criteria (MySQL vs none).

### 12.4 Vedaws awareness (planning only)

Planner does not invoke Vedaws. Planner **aligns** phase vocabulary with:

```
scope → architecture → api-design → implement → test → review → handoff
```

Documenter/submission is **outside** Vedaws workflow — BACKLOG only.

---

## 13. Planning Constraints

### 13.1 Dependency constraints

| Constraint | Source |
|------------|--------|
| Software workflow `depends_on` chain | `software.workflow.toml` |
| Design before UI implement | `paws022/docs/UI_DESIGN.md` |
| Documenter last | `paws022/docs/SUBMISSION_DOCUMENTATION.md` |
| One active CURRENT TASK | Executor spec §4.4 |

### 13.2 Scope constraints

| Constraint | Rule |
|------------|------|
| MVP first | Phase 1 minimal |
| No big-bang | Split implement |
| Rubric alignment | Map criteria to phases |
| Frozen trees | Never plan edits to `vedaws/` or PAWS kernel |
| Userspace | Plan code only under `main/src/` (sidecar) |

### 13.3 Stack constraints

| Topic | Rule |
|-------|------|
| Database | MySQL default if DB needed and unstated (`planner_prompt.md`); honor user SQLite/Postgres/file-only if stated |
| Auth | Plan only if assignment requires |
| External APIs | Name integration; no invented keys |

### 13.4 Time constraints

If deadline is tight:

- Collapse scope in Notes; do not skip handoff or documenter BACKLOG item
- Prefer fewer implement phases with narrower acceptance criteria
- Never remove human test gate

---

## 14. Acceptance Criteria Generation

### 14.1 Properties

Every criterion must be:

| Property | Meaning |
|----------|---------|
| **Testable** | Human or Executor can verify pass/fail |
| **In-scope** | Achievable in one Master Prompt cycle |
| **Specific** | Files, endpoints, screens, or behaviors named |
| **Independent** | Checkbox stands alone |

### 14.2 Anti-patterns (forbidden)

| Bad criterion | Why |
|---------------|-----|
| "Make it work" | Not testable |
| "Complete the entire app" | Multi-phase cramming |
| "Follow best practices" | Not verifiable |
| "Add tests" (without what) | Vague |

### 14.3 Good patterns

```markdown
- [ ] `paws022/docs/architecture.md` describes at least 3 components and data flow
- [ ] `main/src/` contains working login route returning 200 for valid credentials
- [ ] `paws022/docs/db_schema.md` documents `users` table matching MySQL conventions
- [ ] `paws022/design/DESIGN.md` status set to `ready for implementation` with screens S1–S3 listed
- [ ] HANDOFF updated with how to run `npm test`
```

### 14.4 Rubric mapping

When rubric provided, include at least one criterion per rubric checkpoint **for this phase**, or note in Notes which rubric items later phases cover.

### 14.5 UI criteria

- Reference screen IDs from DESIGN.md when they exist
- If design phase: criteria target DESIGN.md completeness, not `src/` UI

---

## 15. Scope Control

### 15.1 Mechanisms

| Mechanism | Application |
|-----------|-------------|
| **Single CURRENT TASK** | One phase per Master Prompt |
| **BACKLOG queue** | Defer all non-urgent work |
| **Constraints: Do not touch** | Explicit file/module exclusions |
| **Implement splits** | Multiple BACKLOG implement items |
| **MVP Phase 1** | Smallest first deliverable |
| **Human gate** | Planner assumes human tests before next prompt |

### 15.2 Scope creep handling

If assignment is large:

1. State total phase estimate in PROJECT BRIEF Notes.
2. Put explicit out-of-scope list in Constraints.
3. Never expand CURRENT TASK because "it's related."

### 15.3 Out-of-scope defaults

Unless assignment requires:

- Production deployment hardening
- Full test coverage
- i18n, accessibility beyond rubric
- Performance optimization beyond stated NFRs

List deferred items in BACKLOG or Notes.

---

## 16. Failure Handling

### 16.1 Insufficient intake

| Situation | Behavior |
|-----------|----------|
| Empty assignment | Ask one clarifying question; do not emit empty Master Prompt |
| Vague "build an app" | Propose scoped MVP in Notes; Phase 1 = scope |
| Missing rubric for coursework | Ask once; proceed with generic BACKLOG document item |

### 16.2 Human follow-up conflicts

| Situation | Behavior |
|-----------|----------|
| Says done but lists open bugs | Next phase = fix implement; carry bugs in acceptance criteria |
| Contradicts prior context | Ask one question; prefer latest human message |
| Wants to skip phases | Allow only if human explicitly accepts risk; note in Constraints |

### 16.3 Orchestration mismatch (reported by human)

If human cites Vedaws doctor/blocker:

- Do not plan new features until recovery phase
- CURRENT TASK = resolve blocker or design gate per human report
- Reference Executor recovery (Executor spec §12)

### 16.4 Unplannable request

| Situation | Behavior |
|-----------|----------|
| "Write my whole report" | Redirect to Documenter + HANDOFF |
| "Fix this one line" | Redirect to Executor chat |
| "Change Vedaws core" | Out of scope; Vespawd does not modify frozen trees |

---

## 17. Recovery Workflow

### 17.1 After blocked phase

Human reports Executor blocked (design, doctor, deps):

```
1. Planner reads Problems + What runs from follow-up
2. CURRENT TASK = recovery-focused (design update, env fix, reduced scope)
3. Constraints include: do not advance to next feature until unblocked
4. BACKLOG unchanged except reprioritize if needed
5. Emit Master Prompt
```

### 17.2 After failed phase (acceptance not met)

```
1. Human lists unmet criteria
2. CURRENT TASK = same phase id with narrowed Goal fixing gaps
3. Constraints: Do not redo completed criteria (list them)
4. Emit Master Prompt
```

### 17.3 After human rejects plan

```
1. Human states rejection reason
2. Planner revises CURRENT TASK only OR full replan if requested
3. Max 3 clarification questions if still blocking
4. Emit new Master Prompt
```

### 17.4 Project restart

If human says start over:

- Treat as new initial plan
- PROJECT BRIEF notes restart
- BACKLOG full sequence
- Constraints: document what to preserve from prior work if anything

---

## 18. Tool Neutrality

### 18.1 Requirements

| Requirement | Detail |
|-------------|--------|
| Terminology | **Planner**, not vendor product names, in spec normative text |
| Output | Identical POS MASTER PROMPT format regardless of model |
| Instructions source | `paws022/.ai/planner_prompt.md` (+ Gem split files if needed) |
| No IDE coupling | Planner never references IDE-specific features as required |
| No Vedaws CLI | Planner does not run or cite CLI commands to human |

### 18.2 Configuration

Humans may configure Planner in any external chat. Reference setup: `paws022/docs/EXTERNAL_AGENTS_SETUP.md`. Compatibility test: output parses successfully per Executor spec §4.

### 18.3 Optional tool features

| Feature | Status |
|---------|--------|
| File upload (Knowledge) | Optional; `planner_prompt_full.txt`, layout docs |
| Web browse | Optional; not required for determinism |
| Memory | Must not replace explicit follow-up template facts |

---

## 19. Design Goals

| Goal | How this spec enforces it |
|------|---------------------------|
| **Deterministic planning** | Fixed output contract, phase algorithm, single CURRENT TASK |
| **Minimal hallucination** | Ground plans in intake/rubric/follow-up; assumptions in Notes |
| **Predictable execution** | Acceptance criteria rules; Executor instruction baseline |
| **Resumable projects** | Follow-up template; short brief on phase 2+ |
| **Project consistency** | Vedaws phase alignment; context merge rules |
| **Maintainability** | Split implement; BACKLOG ordering |
| **PAWS compatibility** | Master Prompt format unchanged |
| **Vedaws compatibility** | Phase id mapping; no `.vedaws` edits |
| **Executor compatibility** | Mirror Executor spec parse sections |
| **Human authority** | Gates between phases; Planner never self-approves |

---

## Appendix A — Master Prompt skeleton

```markdown
# POS MASTER PROMPT

## PROJECT BRIEF

<assignment summary; phase role>

## PROJECT CONTEXT UPDATES

- **Mode:** sidecar
- **POS folder:** paws022/
- **Application code:** main/src/
- ...

## CURRENT TASK

Status: in_progress

### Goal

...

### Constraints

- ...

### Acceptance criteria

- [ ] ...

### Notes

- Vedaws phase: software.<id>

## BACKLOG ITEMS

- [ ] **...** — ... _(priority: ...)_
- [ ] **Submission documentation** — Documenter + HANDOFF + rubric _(priority: low)_

## EXECUTOR INSTRUCTIONS

1. Merge PROJECT CONTEXT UPDATES into paws022/.ai/project_context.md
2. Write CURRENT TASK to paws022/tasks/current_task.md
3. ...
```

---

## Appendix B — Vedaws software phase map

| Vedaws task id | depends_on | Planner BACKLOG order |
|----------------|------------|----------------------|
| `scope` | — | First (or CURRENT TASK) |
| `architecture` | scope | After scope |
| `api-design` | architecture | After architecture |
| `implement` | api-design | After api-design; may repeat |
| `test` | implement | After implement |
| `review` | test | After test |
| `handoff` | review | Before documenter item |
| *(documenter)* | handoff complete | **Last BACKLOG item only** |

Source: `vedaws/plugins/software/templates/project/workflows/software.workflow.toml`

---

## Appendix C — UI-heavy planning checklist

- [ ] Assignment requires UI?
- [ ] If yes: design-only phase in BACKLOG before screen implement?
- [ ] Screen names listed (not tool prompts)?
- [ ] `design/DESIGN.md` referenced in Constraints?
- [ ] Implement split per screen group if >3 screens?
- [ ] API-only paths excluded from UI phases?

Source: `paws022/docs/UI_DESIGN.md`

---

## Appendix D — Planner ↔ Executor handoff checklist

Before emitting, Planner verifies:

- [ ] H1 is first line
- [ ] All six sections present
- [ ] CURRENT TASK has Status, Goal, Constraints, Acceptance criteria, Notes
- [ ] Exactly one phase in CURRENT TASK
- [ ] BACKLOG ends with submission/documentation when coursework
- [ ] No implementation code
- [ ] No "edit current_task.md manually"
- [ ] EXECUTOR INSTRUCTIONS numbered
- [ ] Userspace path is `main/src/` (Vespawd sidecar)
- [ ] Phase id in Notes matches Vedaws software workflow (when applicable)

Executor validation: [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md) §4.7

---

## Appendix E — Related documents

| Document | Role |
|----------|------|
| [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) | System integration, phase map |
| [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md) | Downstream parse and behavior |
| [START_HERE.md](START_HERE.md) | Human-facing workflow |
| `paws022/.ai/planner_prompt.md` | Baseline prompt text |
| `paws022/.ai/planner_followup_message.md` | Follow-up template |
| `paws022/docs/EXECUTOR_LOOP.md` | Phase loop after first prompt |
| `paws022/docs/SUBMISSION_DOCUMENTATION.md` | Documenter last |

---

*Canonical Vespawd Planner Specification. Design only — no implementation.*
