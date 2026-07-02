"""Master Prompt parse engine (Executor Spec §4)."""

from __future__ import annotations

from vespawd_executor.parse.backlog import parse_backlog_items
from vespawd_executor.parse.context_updates import parse_context_updates
from vespawd_executor.parse.current_task import parse_current_task
from vespawd_executor.parse.instructions import detect_instruction_conflicts, parse_executor_instructions
from vespawd_executor.parse.phase_hint import extract_phase_hint
from vespawd_executor.parse.sections import (
    EXECUTOR_INSTRUCTIONS_ALIASES,
    get_section,
    split_sections,
    validate_section_order,
)
from vespawd_executor.parse.types import DocumentKind, ParseResult, ParsedMasterPrompt


def parse_master_prompt(text: str) -> ParseResult:
    """
    Parse a POS MASTER PROMPT document (§4).

    On failure (§4.7): ok=False with errors and missing_sections; no side effects.
    """
    result = ParseResult(ok=False)

    if not text or not text.strip():
        result.errors.append("Empty Master Prompt body")
        return result

    # Lazy import avoids a package import cycle (parse -> startup.trigger -> api -> parse).
    from vespawd_executor.startup.trigger import is_master_prompt

    if not is_master_prompt(text):
        result.errors.append("Document is not a recognized Master Prompt (§3.1)")
        return result

    section_map, split_errors = split_sections(text)
    if section_map is None:
        result.errors.extend(split_errors)
        result.missing_sections = _missing_from_errors(split_errors)
        return result

    warnings: list[str] = []
    if section_map.preamble.strip():
        warnings.append("Content before H1 detected; Planner contract forbids preamble")

    order_errors = validate_section_order(section_map.sections)
    if order_errors:
        result.errors.extend(order_errors)
        result.missing_sections = [
            e.removeprefix("Missing required section: ")
            for e in order_errors
            if e.startswith("Missing required section:")
        ]
        return result

    if split_errors:
        result.errors.extend(split_errors)
        if any("before H1" in e for e in split_errors):
            return result

    brief = get_section(section_map.sections, "PROJECT BRIEF")
    context_body = get_section(section_map.sections, "PROJECT CONTEXT UPDATES")
    task_body = get_section(section_map.sections, "CURRENT TASK")
    backlog_body = get_section(section_map.sections, "BACKLOG ITEMS")
    instructions_body = ""
    for alias in EXECUTOR_INSTRUCTIONS_ALIASES:
        instructions_body = get_section(section_map.sections, alias)
        if instructions_body:
            break

    current_task, task_errors = parse_current_task(task_body)
    if task_errors:
        result.errors.extend(task_errors)
        return result

    assert current_task is not None
    context = parse_context_updates(context_body)
    backlog = parse_backlog_items(backlog_body)
    instructions = parse_executor_instructions(instructions_body)
    phase_hint = extract_phase_hint(current_task.notes, current_task.goal)
    conflicts = detect_instruction_conflicts(instructions, current_task.acceptance_items)

    document_kind = (
        DocumentKind.LEGACY_CURSOR
        if section_map.document_kind == "legacy"
        else DocumentKind.POS
    )

    result.parsed = ParsedMasterPrompt(
        document_kind=document_kind,
        project_brief=brief,
        project_context=context,
        current_task=current_task,
        backlog_items=backlog,
        executor_instructions=instructions,
        phase_hint=phase_hint,
        instruction_conflicts=conflicts,
        warnings=warnings,
    )
    result.ok = True
    return result


def _missing_from_errors(errors: list[str]) -> list[str]:
    missing: list[str] = []
    for error in errors:
        if error.startswith("Missing required section:"):
            missing.append(error.removeprefix("Missing required section: "))
        elif "Missing H1" in error:
            missing.append("POS MASTER PROMPT (H1)")
        elif "No H2 sections" in error:
            missing.extend(
                [
                    "PROJECT BRIEF",
                    "PROJECT CONTEXT UPDATES",
                    "CURRENT TASK",
                    "BACKLOG ITEMS",
                    "EXECUTOR INSTRUCTIONS",
                ]
            )
    return missing


def to_ingest_payload(parsed: ParsedMasterPrompt) -> dict:
    """Shape parsed sections for bridge.ingest_master_prompt (Phase 4; no Bridge call here)."""
    payload: dict = {
        "current_task": {
            "goal": parsed.current_task.goal,
            "acceptance_criteria": parsed.current_task.acceptance_criteria,
        },
    }
    if parsed.current_task.constraints:
        payload["current_task"]["constraints"] = parsed.current_task.constraints
    if parsed.current_task.notes:
        payload["current_task"]["notes"] = parsed.current_task.notes
    if parsed.project_context.product_name:
        payload["project_context"] = {"product_name": parsed.project_context.product_name}
    if parsed.phase_hint:
        payload["phase_hint"] = parsed.phase_hint
    return payload
