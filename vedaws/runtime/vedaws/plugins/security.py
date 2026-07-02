"""Plugin security policy helpers."""

from __future__ import annotations

from vedaws.plugins.manifest import PluginSecurity

ALLOWED_PLUGIN_PERMISSIONS: set[str] = {
    "filesystem.read",
    "filesystem.write",
    "subprocess.exec",
    "network.outbound",
}

ALLOWED_NETWORK_MODES: set[str] = {"none", "outbound"}


def validate_security_declaration(security: PluginSecurity) -> list[str]:
    errors: list[str] = []
    unknown = sorted(
        permission
        for permission in security.permissions
        if permission not in ALLOWED_PLUGIN_PERMISSIONS
    )
    if unknown:
        errors.append(f"unknown security permissions: {', '.join(unknown)}")

    if security.network not in ALLOWED_NETWORK_MODES:
        errors.append(
            f"invalid security.network '{security.network}' (expected one of: none, outbound)"
        )

    if security.subprocess_allow and "subprocess.exec" not in security.permissions:
        errors.append("security.subprocess_allow requires 'subprocess.exec' permission")

    if security.network == "outbound" and "network.outbound" not in security.permissions:
        errors.append("security.network='outbound' requires 'network.outbound' permission")

    return errors
