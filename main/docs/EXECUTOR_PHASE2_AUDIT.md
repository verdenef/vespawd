# Executor Phase 2 Audit

**Date:** 2026-07-01  
**Scope:** Executor Spec §4 (Master Prompt Parsing), Planner Spec §5–10 output contract  
**Package:** `main/executor/lib/vespawd_executor/parse/`  
**Tests:** 44/44 passing (`python -m pytest` in `main/executor/`)

---

## Requirements traceability

| Spec ref | Requirement | Implementation | Test | Status |
|----------|-------------|----------------|------|--------|
| §4.1 | H1 `# POS MASTER PROMPT` in order | `parse/sections.py` `locate_h1()` | `test_sections.py` | Pass |
| §4.1 | Legacy H1 `# CURSOR MASTER PROMPT` | `parse/sections.py` | `legacy_master_prompt.md` | Pass |
| §4.1 | Required H2 sections in order | `validate_section_order()` | `test_sections.py` | Pass |
| §4.1 | No content before H1 (Planner contract) | `split_sections()` error + warning in engine | `test_sections.py` | Pass |
| §4.1 | Legacy `CURSOR INSTRUCTIONS` alias | `EXECUTOR_INSTRUCTIONS_ALIASES` | `test_instructions.py` | Pass |
| §4.2 | Extract PROJECT BRIEF | `parse/engine.py` | `test_parse_engine.py` | Pass |
| §4.3 | Parse PROJECT CONTEXT UPDATES fields | `parse/context_updates.py` | `test_context_updates.py` | Pass |
| §4.4 | CURRENT TASK Status, Goal, Constraints, Criteria, Notes | `parse/current_task.py` | `test_current_task.py` | Pass |
| §4.4 | Exactly one goal; checkbox acceptance criteria | `parse/current_task.py` | `test_current_task.py` | Pass |
| §4.5 | Parse BACKLOG ITEMS; skip duplicate titles | `parse/backlog.py` | `test_backlog.py` | Pass |
| §4.6 | Parse numbered EXECUTOR INSTRUCTIONS | `parse/instructions.py` | `test_instructions.py` | Pass |
| §4.6 | Instructions vs criteria conflict heuristic | `detect_instruction_conflicts()` | `test_instructions.py` | Pass |
| §4.7 | Fail on missing sections / incomplete CURRENT TASK | `parse/engine.py` | `test_parse_engine.py` | Pass |
| §4.7 | No side effects on parse failure | Pure parse functions | — | Pass |
| Planner §5.1 | CURRENT TASK H3 structure | `parse/current_task.py` | `test_current_task.py` | Pass |
| Planner §6.1 | Structured backlog item format | `parse/backlog.py` | `test_backlog.py` | Pass |
| Planner §10 | Output contract sections | Golden fixtures | `test_parse_engine.py` | Pass |
| Architecture §6 | Phase hint for Vedaws mapping | `parse/phase_hint.py` | `test_phase_hint.py` | Pass |

---

## Public API

| Symbol | Purpose |
|--------|---------|
| `parse_master_prompt(text) -> ParseResult` | Main entry; §4.7 failure semantics |
| `to_ingest_payload(parsed) -> dict` | Bridge `ingest_master_prompt` input shape (used in Phase 4) |
| `ParsedMasterPrompt`, `ParseResult`, etc. | Typed parse output |

---

## Deferred to later phases

| Spec ref | Requirement | Phase |
|----------|-------------|-------|
| §4.3 | Merge into `project_context.md` | Phase 3 |
| §4.4 | Write `current_task.md` with Started date | Phase 3 |
| §4.5 | Append `backlog.md` | Phase 3 |
| §4.6 | Note conflicts in `current_task.md` Notes | Phase 3 |
| §4.3 / §5.3 | `bridge.ingest_master_prompt` | Phase 4 |
| §4.2 | HANDOFF seed from brief | Phase 7 |

---

## Documented ambiguities (not invented)

| ID | Topic | Phase 2 handling |
|----|-------|------------------|
| A-03 | §4.5 backlog in bridge manifest | Not parsed into manifest; backlog list only in `ParsedMasterPrompt` for Phase 3 writer |
| A-04 | §4.6 full conflict resolution | Conservative keyword heuristic; Executor judgment deferred |
| A-05 | Status values other than `in_progress` | Treated as parse error (Planner §5.2 requires `in_progress`) |
| A-06 | Preamble + explicit execute phrase (§3.1) | `is_master_prompt` true via phrase but parse warns/errors on content before H1 |

---

## Gaps / notes

| Item | Classification | Note |
|------|----------------|------|
| PAWS file writes | Deferred | Phase 2 is parse-only per plan |
| Empty EXECUTOR INSTRUCTIONS body | Allowed | Section must exist; empty list is valid |
| Simple `- [ ]` backlog lines | Supported | In addition to Planner structured format |
| `to_ingest_payload()` | Phase 4 prep | No Bridge invocation in Phase 2 |

---

## Phase 2 verdict

**PASS** — Master Prompt parsing complete per §4. Safe to proceed to **Phase 3** (PAWS synchronization writers, §5).

---

*Stop here per phased implementation plan. Do not begin Phase 3 until approved.*
