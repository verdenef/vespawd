# Decisions (POS Memory)

Architecture Decision Records (ADRs) for **this repository**. The template below is stable; entries are per-project.

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| ADR-001 | _{e.g. Adopt POS template}_ | accepted | |

## ADR Template

```markdown
### ADR-NNN: Title

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | deprecated | superseded by ADR-XXX

**Context**
Why we needed a decision.

**Decision**
What we chose.

**Consequences**
Tradeoffs and follow-ups.
```

---

## Entries

### ADR-001: Adopt Project Operating System layout

**Date:** _{bootstrap date}_  
**Status:** accepted

**Context**

Need a consistent layout and agent playbook for every new project.

**Decision**

Use POS: `.ai/` kernel, `docs/` memory, `tasks/` scheduler, `src/` userspace.

**Consequences**

- Onboarding and agents follow the same read order every repo.
- Kernel updates propagate by merging template changes.

_Add ADR-002+ below as the project evolves._
