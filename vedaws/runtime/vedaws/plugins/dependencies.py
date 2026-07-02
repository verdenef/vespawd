"""Plugin dependency resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.versioning import satisfies_constraint


@dataclass
class DependencyResolutionResult:
    order: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def resolve_dependencies(
    manifests: dict[str, PluginManifest],
    *,
    selected_ids: set[str] | None = None,
) -> DependencyResolutionResult:
    result = DependencyResolutionResult()
    targets = selected_ids or set(manifests.keys())

    for plugin_id in targets:
        manifest = manifests.get(plugin_id)
        if manifest is None:
            result.errors.append(f"Plugin '{plugin_id}' not found")
            continue
        for dep in manifest.dependencies:
            if dep.id not in manifests:
                result.errors.append(
                    f"Plugin '{plugin_id}' requires missing dependency '{dep.id}'"
                )
                continue
            dep_manifest = manifests[dep.id]
            if not satisfies_constraint(dep_manifest.version, dep.version):
                result.errors.append(
                    f"Plugin '{plugin_id}' requires '{dep.id}' {dep.version} "
                    f"(found {dep_manifest.version})"
                )

    if result.errors:
        return result

    graph = {plugin_id: [] for plugin_id in targets}
    for plugin_id in targets:
        manifest = manifests[plugin_id]
        for dep in manifest.dependencies:
            if dep.id in targets:
                graph[plugin_id].append(dep.id)

    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> bool:
        if node in visiting:
            cycle = " -> ".join([*stack, node])
            result.errors.append(f"Circular plugin dependency: {cycle}")
            return False
        if node in visited:
            return True
        visiting.add(node)
        for dep in graph.get(node, []):
            if not visit(dep, [*stack, node]):
                return False
        visiting.remove(node)
        visited.add(node)
        order.append(node)
        return True

    for plugin_id in sorted(targets):
        if plugin_id not in visited:
            if not visit(plugin_id, []):
                return result

    result.order = order
    return result
