"""Health check result model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: CheckStatus
    message: str

    @property
    def ok(self) -> bool:
        return self.status == CheckStatus.PASS

    @property
    def warning(self) -> bool:
        return self.status == CheckStatus.WARN

    @property
    def failed(self) -> bool:
        return self.status == CheckStatus.FAIL
