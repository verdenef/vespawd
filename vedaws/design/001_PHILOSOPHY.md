# Vedaws Philosophy

**Version:** 0.5.0

**Status:** Stable — principles validated through Milestone 12 implementation

## Purpose

This document defines the philosophical foundation of Vedaws. It translates the Vision into durable beliefs, role boundaries, and decision rules that govern every future architectural choice.

Vedaws is a domain-neutral Development Operating System. Its purpose is to reduce developer cognitive load by taking responsibility for coordination — remembering project state, deciding what happens next within agreed workflows, and dispatching work to the right executors — while leaving judgment, ownership, and creative authority with humans.

Vedaws exists because modern development, especially with AI assistance, pushes coordination onto the developer. The developer becomes the implicit runtime: tracking context, sequencing tasks, reconciling outputs, and keeping workflows consistent across tools and conversations. Vedaws exists to become that runtime explicitly, so developers can focus on problems worth solving.

The ideal relationship is simple:

The developer decides.

Vedaws orchestrates.

Workers execute.

---

## The Role of Humans

Humans are the source of intent, judgment, and accountability in every Vedaws project.

Humans define what is being built and why. They set product vision, architectural direction, creative standards, priorities, and acceptance criteria. They resolve ambiguity, weigh tradeoffs, and approve outcomes that matter.

Vedaws must never absorb ownership that belongs to humans. When a decision carries strategic, architectural, or creative weight, the system must surface it for human judgment rather than resolve it silently. When a decision is reversible and low-risk, Vedaws may proceed within defined boundaries.

Humans may also act as workers. A human performing a task is not a failure of automation; it is a valid execution path. The runtime treats human participation as first-class, not as a fallback to be minimized at all costs.

The measure of success is not how much humans are removed from the loop. The measure is how much unnecessary coordination burden is removed from them.

---

## The Role of Workers

Workers are the executors of work.

A worker is any entity capable of performing a bounded unit of work: generating code, running checks, updating documentation, invoking a tool, applying a transformation, or carrying out a human-assigned task. Workers may be AI systems, development tools, scripts, services, or people.

Workers do not own project direction. They receive context, instructions, and constraints from the runtime and return results. They are interchangeable at the boundary of their capability: the runtime should not depend on *who* performed the work, only on *what* was produced and whether it satisfies the task.

Workers may be specialized. Domain knowledge belongs at the worker and plugin layer, not in the assumption that only one kind of worker can ever exist. The runtime coordinates workers; it does not pretend to be one.

Multiple workers may collaborate on a workflow, sequentially or in parallel, as orchestration requires. The runtime is responsible for handoffs, dependencies, and consistency between worker outputs.

---

## The Role of Automation

Automation handles work that is deterministic, repeatable, and low-risk.

When a task follows a known pattern, does not require novel judgment, and produces outcomes that can be verified mechanically, Vedaws should prefer automation over manual repetition. Automation exists to eliminate toil — the coordination and execution work that adds no creative or strategic value.

Automation is not the same as intelligence. A task may be automated without being "smart," and a task may require a worker without being fully automatable. Vedaws distinguishes between *what must happen* and *how much judgment it requires*.

Automation must remain subordinate to human authority. Automated actions that affect project state, artifacts, or workflow progression must be traceable, bounded by policy, and reversible where practical. Automation reduces effort; it does not transfer accountability away from humans.

When automation is uncertain, incomplete, or high-impact, it must defer to human review rather than proceed optimistically.

---

## The Role of the Runtime

The runtime is the coordination layer.

It maintains project state, interprets where a project is in its workflow, decides what may happen next, dispatches work to workers, records outcomes, and enforces consistency across the lifecycle of a project. It is the explicit embodiment of the coordination burden developers currently carry informally.

The runtime does not replace development tools, version control, AI models, game engines, or IDEs. It sits above them as the system that knows what the project is trying to accomplish and how the pieces of work fit together.

The runtime must remain small in ambition and large in reach. Its responsibility is orchestration — sequencing, state, policy, and handoff — not domain expertise. Domain behavior extends outward through plugins and workers; the runtime provides the stable center.

The runtime is state-driven. Decisions about what to do next arise from explicit project state, not from hidden assumptions, stale context, or implicit memory held only in conversation. If the runtime cannot determine state confidently, it must ask rather than guess.

The runtime must be domain-neutral at its core. It orchestrates development work regardless of language, framework, engine, or toolchain. Specificity belongs at the edges.

---

## Orchestration Over Automation

Automation answers: *How do I do this task again without thinking?*

Orchestration answers: *What needs to happen next, who should do it, and how does it fit the whole project?*

Vedaws is founded on orchestration because the central failure mode of modern AI-assisted development is not lack of capability — it is lack of coordination. Individual tools automate fragments well. Developers still manually stitch those fragments into a coherent project lifecycle.

A collection of automations without orchestration produces more surface area, not less cognitive load. Each automation must still be remembered, invoked, sequenced, and reconciled. The developer remains the runtime.

Orchestration treats the project as a whole. It connects tasks into workflows, workflows into phases, and phases into a durable model of project progress. Automation is a mechanism inside that model — often the right mechanism — but not the organizing principle.

"Orchestrate work. Not just code." means Vedaws coordinates the full scope of development activity: planning, implementation, verification, documentation, artifact management, and project health — not only the moment of writing source code.

Orchestration also implies discipline about boundaries. The runtime coordinates; workers execute; humans decide. Blurring these roles creates systems that act without accountability or automate without context.

The philosophical priority is therefore:

1. Make project state explicit.
2. Make workflow progression legible.
3. Dispatch the right work to the right executor.
4. Automate within that structure wherever safe and practical.

Automation serves orchestration. Orchestration serves human intent.

---

## Design Principles

Every future feature, subsystem, and extension must obey these principles. They are the test applied before any design is accepted.

### 1. Domain Neutrality

The core must not assume a specific technology, language, framework, or development domain. Domain specificity belongs in plugins and workers.

### 2. Human Authority Over Judgment

Humans retain final authority over vision, architecture, creativity, priorities, and acceptance. Features that remove or obscure human decision points on matters of judgment violate Vedaws philosophy.

### 3. Explicit State

Project progress must be representable as explicit state. Behavior should be derived from state, not from implicit context scattered across tools and conversations.

### 4. Separation of Coordination and Execution

The runtime coordinates. Workers execute. Features must preserve this boundary unless there is an exceptional, documented reason not to.

### 5. Automation With Accountability

Automated behavior must be traceable, policy-bounded, and appropriate to risk. High-impact or ambiguous actions require human visibility.

### 6. Reproducibility

Given the same project state, workflow definition, and inputs, Vedaws should produce consistent outcomes whenever practical. Non-determinism must be intentional, visible, and constrained.

### 7. Small Core, Extensible Edge

The runtime stays minimal. Domain behavior, tool integration, and specialized capability grow through plugins and workers, not through core bloat.

### 8. Replaceability of Workers

No feature may hard-bind the system to a single executor. Workers are interchangeable within their declared capabilities.

### 9. Legibility Over Opacity

Developers must be able to understand what Vedaws is doing and why. Features that hide workflow progression, state changes, or automated actions behind opaque behavior are unacceptable.

### 10. Reduce Coordination, Not Responsibility

Vedaws removes unnecessary coordination work. It does not remove human ownership of outcomes.

When a proposed feature conflicts with these principles, the feature must be redesigned or rejected — not the principles.

---

## Anti-Goals

The following describe what Vedaws must never become. They are as important as the goals.

### Vedaws must never become a developer replacement.

It coordinates and reduces toil. It does not assume creative, architectural, or strategic authority that belongs to humans.

### Vedaws must never become another AI wrapper.

A thin interface around a model is not an operating system. Vedaws is not defined by prompting alone; it is defined by orchestration, state, and workflow discipline.

### Vedaws must never become a prompt collection.

Reusable prompts may exist as artifacts or worker inputs, but prompt libraries are not a substitute for project coordination.

### Vedaws must never become an IDE, engine, or framework.

It must not attempt to replace the environments where work is performed. It coordinates across them.

### Vedaws must never become a chatbot-first product.

Conversation may be one interface, but Vedaws is not reducible to chat. Its center of gravity is project state and workflow orchestration.

### Vedaws must never become a black box.

If the system cannot explain what it did, why it did it, and what changed, it has failed its coordination role.

### Vedaws must never become domain-specific at the core.

Optimizing the runtime for one stack, engine, or workflow pattern at the expense of neutrality fractures the DevOS into a niche tool.

### Vedaws must never become autonomous without governance.

Proactive behavior is welcome when bounded. Ungoverned autonomy that changes project state, artifacts, or direction without visibility violates human authority.

### Vedaws must never become complexity disguised as automation.

Adding orchestration layers that increase cognitive load rather than reduce it betrays the mission. Every feature must justify itself by removing coordination burden.

### Vedaws must never become the owner of truth it does not maintain.

Vedaws coordinates project state, but it must not claim authority over external systems it does not govern. It integrates with sources of truth; it does not pretend to replace them all.

---

## TODO

- Align terminology with `002_CORE.md` once core concepts are defined. ✅
- Reconcile principle numbering with downstream design documents as they are authored. ✅
- Review anti-goals after `015_ROADMAP.md` to ensure scope boundaries remain consistent. ✅ (roadmap populated at v0.5 freeze)
