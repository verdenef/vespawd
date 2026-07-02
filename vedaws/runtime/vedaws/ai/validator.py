"""AI provider validation for diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field

from vedaws.ai.config import AIConfig
from vedaws.ai.registry import AIProviderRegistry


@dataclass
class AIValidationIssue:
    message: str
    severity: str = "error"
    provider_id: str = ""
    capability: str = ""


@dataclass
class AIValidationReport:
    issues: list[AIValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")


def validate_ai_platform(
    registry: AIProviderRegistry,
    config: AIConfig,
) -> AIValidationReport:
    report = AIValidationReport()

    if registry.count == 0:
        report.issues.append(
            AIValidationIssue("No AI providers registered", severity="warning")
        )
        return report

    if config.default_provider and registry.get(config.default_provider) is None:
        report.issues.append(
            AIValidationIssue(
                f"Configured default provider '{config.default_provider}' is not registered",
                provider_id=config.default_provider,
            )
        )

    for capability, routing in config.capabilities.items():
        chain = []
        if routing.preferred:
            chain.append(routing.preferred)
        chain.extend(routing.fallback)
        for provider_id in chain:
            provider = registry.get(provider_id)
            if provider is None:
                report.issues.append(
                    AIValidationIssue(
                        f"Fallback chain references unknown provider '{provider_id}'",
                        provider_id=provider_id,
                        capability=capability,
                    )
                )
                continue
            if not provider.supports_capability(capability):
                report.issues.append(
                    AIValidationIssue(
                        f"Provider '{provider_id}' does not support capability '{capability}'",
                        severity="warning",
                        provider_id=provider_id,
                        capability=capability,
                    )
                )

    for provider in registry.list_providers():
        health = provider.health()
        if not health.healthy:
            report.issues.append(
                AIValidationIssue(
                    health.message or "Provider unhealthy",
                    severity="warning",
                    provider_id=provider.id,
                )
            )
        if not health.credentials_available:
            report.issues.append(
                AIValidationIssue(
                    "Credentials not available",
                    severity="warning",
                    provider_id=provider.id,
                )
            )

    return report
