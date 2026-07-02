# Architecture Escalation Rules

Before making a design decision, ask:

1. Does this change the philosophy?
2. Does this introduce a new core concept?
3. Does this change the runtime?
4. Does this change worker responsibilities?
5. Does this affect plugin compatibility?
6. Does this reduce domain neutrality?
7. Does this change project state semantics?

If YES to any:

Stop.

Mark the document:

ARCHITECTURE REVIEW REQUIRED

Do not continue implementing until reviewed.

Otherwise:

Continue normally.