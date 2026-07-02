"""Parsed Master Prompt types (Executor Spec §4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DocumentKind(str, Enum):
    POS = "pos_master_prompt"
    LEGACY_CURSOR = "legacy_cursor_master_prompt"


@dataclass(frozen=True)
class CurrentTaskParsed:
    status: str
    goal: str
    constraints: str
    acceptance_criteria: str
    notes: str
    acceptance_items: tuple[str, ...] = ()


@dataclass(frozen=True)
class BacklogItemParsed:
    title: str
    description: str
    priority: str | None = None
    raw_line: str = ""


@dataclass(frozen=True)
class ContextUpdatesParsed:
    raw: str
    product_name: str | None = None
    mode: str | None = None
    application_code: str | None = None
    pos_folder: str | None = None
    database: str | None = None
    bullets: tuple[str, ...] = ()


@dataclass
class ParsedMasterPrompt:
    document_kind: DocumentKind
    project_brief: str
    project_context: ContextUpdatesParsed
    current_task: CurrentTaskParsed
    backlog_items: list[BacklogItemParsed] = field(default_factory=list)
    executor_instructions: list[str] = field(default_factory=list)
    phase_hint: str | None = None
    instruction_conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    parsed: ParsedMasterPrompt | None = None

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "missing_sections": list(self.missing_sections),
            "parsed": None if self.parsed is None else _parsed_to_dict(self.parsed),
        }


def _parsed_to_dict(parsed: ParsedMasterPrompt) -> dict:
    return {
        "document_kind": parsed.document_kind.value,
        "project_brief": parsed.project_brief,
        "phase_hint": parsed.phase_hint,
        "current_task": {
            "status": parsed.current_task.status,
            "goal": parsed.current_task.goal,
            "constraints": parsed.current_task.constraints,
            "acceptance_criteria": parsed.current_task.acceptance_criteria,
            "notes": parsed.current_task.notes,
            "acceptance_items": list(parsed.current_task.acceptance_items),
        },
        "backlog_items": [
            {
                "title": item.title,
                "description": item.description,
                "priority": item.priority,
            }
            for item in parsed.backlog_items
        ],
        "executor_instructions": list(parsed.executor_instructions),
        "instruction_conflicts": list(parsed.instruction_conflicts),
        "warnings": list(parsed.warnings),
    }
