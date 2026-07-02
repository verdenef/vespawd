"""AI CLI reporting."""

from __future__ import annotations

from vedaws.ai.model import AIProviderHealth
from vedaws.ai.provider import AIProvider
from vedaws.ai.service import AIService
from vedaws.ai.validator import AIValidationReport


def format_provider_list(service: AIService) -> str:
    lines = ["AI providers:", ""]
    providers = service.list_providers()
    if not providers:
        lines.append("  (none registered — enable an AI provider plugin)")
        return "\n".join(lines)

    default_id = service.registry.default_provider_id
    lines.append(f"  {'ID':<16} {'PRIORITY':<9} {'DEFAULT':<8} CAPABILITIES")
    lines.append(f"  {'-' * 16} {'-' * 9} {'-' * 8} {'-' * 24}")
    for provider in providers:
        default = "yes" if provider.id == default_id else ""
        caps = ", ".join(provider.capabilities)
        lines.append(
            f"  {provider.id:<16} {provider.priority:<9} {default:<8} {caps}"
        )
        lines.append(f"    {provider.name}")
    return "\n".join(lines)


def format_capability_map(service: AIService) -> str:
    lines = ["AI capabilities:", ""]
    mapping = service.list_capabilities()
    if not mapping:
        lines.append("  (no capabilities registered)")
        return "\n".join(lines)

    for capability, provider_ids in mapping.items():
        chain = service.resolve_chain(capability)
        selected = chain[0].id if chain else "-"
        lines.append(f"  {capability}")
        lines.append(f"    providers: {', '.join(provider_ids)}")
        lines.append(f"    selected:  {selected}")
        if len(chain) > 1:
            lines.append(f"    fallback:  {', '.join(item.id for item in chain[1:])}")
    return "\n".join(lines)


def format_ai_status(
    service: AIService,
    health_results: list[AIProviderHealth],
    validation: AIValidationReport,
) -> str:
    lines = ["AI platform status:", ""]
    lines.append(f"  Providers: {service.registry.count}")
    lines.append(f"  Capabilities: {len(service.list_capabilities())}")
    if service.registry.default_provider_id:
        lines.append(f"  Default: {service.registry.default_provider_id}")
    lines.append("")
    lines.append("Provider health:")
    for health in health_results:
        cred = "creds ok" if health.credentials_available else "no creds"
        state = "healthy" if health.healthy else "unhealthy"
        lines.append(f"  [{state}] {health.provider_id} ({cred}) — {health.message}")
    if validation.issues:
        lines.extend(["", "Validation:"])
        for issue in validation.issues:
            scope = issue.capability or issue.provider_id or "platform"
            lines.append(f"  [{issue.severity}] {scope}: {issue.message}")
    return "\n".join(lines)
