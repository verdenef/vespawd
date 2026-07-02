# Architecture Rules (POS Kernel)

Default boundaries for any project using this template. **Project-specific** topology and diagrams live in `docs/architecture.md`.

## Principles

1. **Separation of concerns** — presentation, application logic, and data access are separate.
2. **Dependency direction** — inner layers do not depend on outer layers.
3. **Explicit boundaries** — cross-layer calls use defined interfaces or DTOs.

## Reference Layering

Adapt names to your stack; keep the dependency direction.

| Layer | Responsibility | May depend on |
|-------|----------------|---------------|
| Presentation | HTTP, CLI, GUI, jobs entry | Application |
| Application | Use cases, orchestration | Domain |
| Domain | Entities, business rules | Nothing external |
| Infrastructure | DB, email, queues, files | Domain (implements ports) |

## Rules

- No business logic in thin handlers; delegate to application services.
- Data access only through infrastructure/repository modules.
- Public API shapes documented in `docs/api_contracts.md`.
- Schema changes update `docs/db_schema.md`; non-trivial choices get an ADR in `docs/decisions.md`.

## Forbidden

- Circular module dependencies.
- Exposing persistence models directly on public APIs without mapping.
- Hard-coded secrets (use environment/config).

## Overrides

If this project needs different layering, document it in `docs/architecture.md` and add an ADR. Do not silently diverge from these rules.
