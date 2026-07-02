"""Composable validation results (§8)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    passed: bool = True
    codes: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def merge(self, other: ValidationResult) -> ValidationResult:
        return ValidationResult(
            passed=self.passed and other.passed,
            codes=self.codes + other.codes,
            messages=self.messages + other.messages,
        )
