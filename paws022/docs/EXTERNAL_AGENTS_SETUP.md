# External agents setup (POS v1.1.7)

Configure **your own** planner and documenter in whatever tools you chose in setup (Gemini, ChatGPT, Claude, etc.). Copy **prompt text** from this repo — do not share personal assistant links.

**UI in Cursor (typical):** [STITCH_CURSOR.md](STITCH_CURSOR.md) — Stitch MCP; prompts in **executor chat**, not planner. Tool-neutral: [UI_DESIGN.md](UI_DESIGN.md).

Run **`Setup-POS.bat`** once per machine (writes `%USERPROFILE%\.pos\config.json`). The setup wizard links to prompt files below for copying into your Gems.

## Planner (external)

**ChatGPT / Claude:** copy the entire file [.ai/planner_prompt.md](../.ai/planner_prompt.md) into Instructions.

**Gemini Gem (recommended split — Save often fails with long markdown):**

| Field | File | Required? |
|-------|------|-----------|
| **Instructions** | [.ai/planner_prompt_gem_instructions.txt](../.ai/planner_prompt_gem_instructions.txt) | Yes (~900 chars, plain text) |
| **Knowledge** | [.ai/planner_prompt_full.txt](../.ai/planner_prompt_full.txt) | **Yes** — full POS rules, paths, format |
| **Knowledge (optional)** | `docs/PROJECT_LAYOUT.md`, `docs/LAZY_WORKFLOW.md` | Helpful |

Do **not** upload `planner_prompt.md` to Knowledge if you use the split above. The short Instructions alone are **not** enough — without `planner_prompt_full.txt` the Gem will ignore paws022 and POS paths.

**Gemini Gem troubleshooting:**

1. Save with **Instructions only** first (smoke test). Then add `planner_prompt_full.txt` to Knowledge and save again.
2. Description: one short line (e.g. “POS planner. Outputs POS MASTER PROMPT.”).
3. Plain text in Instructions — no markdown headers, backticks, or code fences.
4. Requires **Gemini Advanced / AI Pro** (free tier may not save Gems).
5. If broken, delete Gem and recreate; copy text from the txt files again.

**Suggested display name** (any label you like): e.g. `Project Planner`

**Suggested description:**

```text
Turns assignments into a POS MASTER PROMPT. Planning only — no implementation code.
```

Must include **OUTPUT CONTRACT:** entire reply starts with `# POS MASTER PROMPT`.

## Gemini Gem — Knowledge (optional)

In Gemini, **Instructions** = full copy of the prompt `.md` file. **Knowledge** = extra files the Gem can read (optional but helpful).

Upload from your **paws022 template clone** (not your app repo unless noted).

### Planner Gem — Knowledge

| Upload? | File | Why |
|--------|------|-----|
| Optional | `docs/LAZY_WORKFLOW.md` | End-to-end lazy pipeline |
| Optional | `docs/EXECUTOR_LOOP.md` | What happens after the first Master Prompt |
| Optional | `docs/PROJECT_LAYOUT.md` | Integrated vs sidecar layouts |
| Usually skip | `.ai/planner_prompt.md` | Already pasted into Instructions |
| Do not upload | App `src/`, `.env`, secrets | Planner must not implement code |

### Documenter Gem — Knowledge

| Upload? | File | Why |
|--------|------|-----|
| Recommended | `docs/SUBMISSION_DOCUMENTATION.md` | Phased report flow + rubric priority |
| Optional | `.ai/documenter_followup_message.md` | Template for section 2+ (paste per turn) |
| Optional | `docs/HANDOFF_FOR_DOCUMENTER.md` | Example handoff shape (real handoff comes from the user each time) |
| Optional | `docs/EXECUTOR_LOOP.md` | Context on when HANDOFF is ready |
| Do not upload | `.ai/documenter_prompt.md` | Already in Instructions |
| Do not upload | Full app codebase | Documenter uses **HANDOFF + rubric** you paste in chat |

### Per assignment (chat, not Knowledge)

| Tool | User attaches in the chat |
|------|---------------------------|
| Planner | Assignment text, rubric, phase note (see [planner_followup_message.md](../.ai/planner_followup_message.md) for phase 2+) |
| Documenter | Filled `docs/HANDOFF_FOR_DOCUMENTER.md` + **rubric**; phased: plan first or one section per message ([documenter_followup_message.md](../.ai/documenter_followup_message.md) for later sections) |

**Phased reports (recommended):** Do **not** ask for the full document in one message. Use one chat turn per section (or “report plan” first). See [SUBMISSION_DOCUMENTATION.md](SUBMISSION_DOCUMENTATION.md). Follow-ups: [.ai/documenter_followup_message.md](../.ai/documenter_followup_message.md).

Knowledge files are **static**; the live HANDOFF in your project updates every phase — always paste the latest HANDOFF into the documenter chat.

## UI designer (optional)

Only for apps with real UI. Skip for APIs/CLI.

Copy [.ai/ui_designer_prompt.md](../.ai/ui_designer_prompt.md) into a separate Gem/GPT (or use `toolchain.uiDesigner: "executor"` and MCP in Cursor — see [UI_DESIGN.md](UI_DESIGN.md)).

**Suggested display name:** e.g. `Project UI Designer`

**Suggested description:**

```text
Produces UI DESIGN BRIEF for design/DESIGN.md. No code. No POS MASTER PROMPT.
```

**Knowledge (optional):** `docs/UI_DESIGN.md`, `design/README.md`

## Documenter (external)

Copy the **entire** file [.ai/documenter_prompt.md](../.ai/documenter_prompt.md) into your documenter tool’s instructions field.

**Suggested display name:** e.g. `Project Documenter`

**Suggested description:**

```text
Writes submission reports from HANDOFF + rubric. Markdown only. No code. No POS MASTER PROMPT.
```

See **Gemini Gem — Knowledge** above for documenter uploads.

## Usage

| Step | Action |
|------|--------|
| 1 | `pos-new my-app` or `pos-adopt` → open in **executor** IDE |
| 2 | Planner + assignment → get `# POS MASTER PROMPT` |
| 2b | (Optional) UI designer → merge into `design/DESIGN.md` — [UI_DESIGN.md](UI_DESIGN.md) |
| 3 | Executor chat: `Execute this.` + pasted prompt |
| 4 | When done → documenter + HANDOFF + rubric — **one section per chat** (or report plan first); see [SUBMISSION_DOCUMENTATION.md](SUBMISSION_DOCUMENTATION.md) |

## Example message (planner)

```text
Phase 1 only. [paste assignment]
```

## When this repo updates

Check `instructionsVersion` in `pos.config.json.example`. If it bumps, re-copy planner, documenter, and (if used) UI designer prompt files into **your** external agents.

Tool-specific steps: [TOOLCHAIN.md](TOOLCHAIN.md).
