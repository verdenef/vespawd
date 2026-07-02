# POS MASTER PROMPT format (Knowledge file for planner Gem)

Upload this file to Gemini Gem Knowledge. Do not paste this into Instructions.

## POS folders (reference)

- project_context.md in .ai folder - product, stack, env
- docs folder - architecture, schema, APIs
- tasks/current_task.md - active task
- tasks/backlog.md - future work
- src or sidecar main/src - application code
- design folder - UI spec when applicable

## Required output sections

The planner reply must use this structure:

POS MASTER PROMPT (H1)

PROJECT BRIEF (H2)
Short summary. Phase 2 and later: brief only, not full assignment repeat.

PROJECT CONTEXT UPDATES (H2)
Bullet updates for project_context.md if stack or layout changes.

CURRENT TASK (H2)
Status: in_progress
Goal (H3)
Constraints (H3)
Acceptance criteria (H3)
Notes (H3)

BACKLOG ITEMS (H2)
Numbered list of future phases. School report documentation is last.

EXECUTOR INSTRUCTIONS (H2)
Numbered list:
1. Merge PROJECT CONTEXT UPDATES into .ai/project_context.md
2. Write CURRENT TASK to tasks/current_task.md
3. Update docs/architecture.md, docs/db_schema.md, docs/api_contracts.md only if needed
4. For UI work, align with design/DESIGN.md
5. Implement in app code path from project context. Minimal diffs.
6. Update docs/HANDOFF_FOR_DOCUMENTER.md with facts from this phase
7. Summarize how to run and test

## Follow-up input

User may paste content from planner_followup_message.md for phase 2 and later. Output only a new POS MASTER PROMPT.
