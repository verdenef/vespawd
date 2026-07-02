# Submission documentation (POS v1.1.7)

## Two kinds

| Kind | Who | When |
|------|-----|------|
| Technical `docs/` | Executor | During build |
| School report | Documenter (external) | **Last** |

## Flow

| Phase | Who |
|-------|-----|
| Build | Executor maintains HANDOFF automatically (often **phased** via POS MASTER PROMPT) |
| Report | Documenter + HANDOFF + rubric → Canvas/Docs (**phased by section**, not one giant paste) |

Executor does **not** write long report prose in HANDOFF.

## Phased report (recommended)

Same idea as executor `tasks/current_task.md` — **one focused chunk per chat turn**.

```text
Turn 1 → Report plan (section list from rubric) OR first section only
Turn 2 → Next section(s) named by user
Turn 3 → … until complete
Turn N → Optional: “merge polish” only if user asks
```

| Do | Don't |
|----|--------|
| One or two rubric sections per message | Full 2,000+ word report in one reply |
| Use [documenter_followup_message.md](../.ai/documenter_followup_message.md) between sections | Regenerate sections already approved |

## Documenter input

1. `docs/HANDOFF_FOR_DOCUMENTER.md` (auto-filled) — **facts** about what was built
2. **Rubric / assignment** — often defines **required sections and format** (this wins over the default outline in `documenter_prompt.md`)
3. Optional: your own outline in the chat (“use these headings: …”)
4. [EXTERNAL_AGENTS_SETUP.md](EXTERNAL_AGENTS_SETUP.md) → documenter Instructions

**Structure rule:** Assignment/rubric/user outline > default section list in the documenter prompt. HANDOFF supplies content; rubric supplies shape.

**UI figures:** If the rubric requires screenshots, use `design/screens/` or paths noted in HANDOFF **UI / design** — documenter should not invent images.

## Example messages (documenter chat)

**Plan only:**

```text
Read the HANDOFF and rubric. Output a numbered report plan (section titles only). Do not write section prose yet.
```

**One section:**

```text
Write ## System design only. Facts from HANDOFF. Next suggested section when done.
```

**Follow-up:**

Paste [documenter_followup_message.md](../.ai/documenter_followup_message.md) with “Already written” and “Section(s) to write now” filled in.

## Optional nudge (executor)

```text
Refresh the documenter handoff and confirm it's ready for submission docs.
```

## Planner / documenter (external)

Create **your own**; copy Instructions from repo ([TOOLCHAIN.md](TOOLCHAIN.md)). For long rubrics, planner may add backlog items per report section — documenter still drafts **one phase at a time** in chat.
