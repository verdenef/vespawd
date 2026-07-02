# POS Kernel (`.ai/`)

Reusable across **all** projects. Do not put product-specific facts here—use `project_context.md`.

| File | Purpose |
|------|---------|
| [system_prompt.md](system_prompt.md) | Agent entrypoint and read order |
| [architecture_rules.md](architecture_rules.md) | Layering and boundaries |
| [coding_rules.md](coding_rules.md) | Baseline code standards |
| [workflow.md](workflow.md) | Task lifecycle |
| [debugging_protocol.md](debugging_protocol.md) | Defect investigation |
| [executor_rules.md](executor_rules.md) | Executor agent (all IDEs) |
| [planner_prompt.md](planner_prompt.md) | External **planner** (ChatGPT / Claude Instructions) |
| [planner_prompt_gem_instructions.txt](planner_prompt_gem_instructions.txt) | **Gemini Gem** Instructions only (short plain text) |
| [planner_prompt_full.txt](planner_prompt_full.txt) | **Gemini Gem** Knowledge — full POS rules (required with split) |
| [planner_prompt_format.md](planner_prompt_format.md) | Legacy short format reference (use planner_prompt_full.txt instead) |
| [documenter_prompt.md](documenter_prompt.md) | External **documenter** Instructions |
| [planner_followup_message.md](planner_followup_message.md) | Phase 2+ message to planner |
| [documenter_followup_message.md](documenter_followup_message.md) | Phase 2+ message to documenter (one section at a time) |
| [ui_designer_prompt.md](ui_designer_prompt.md) | Optional external **UI designer** (UI DESIGN BRIEF → `design/`) |
| [project_context.md](project_context.md) | **Memory** — fill per project |

Template docs: [../README.md](../README.md), bootstrap: [../BOOTSTRAP.md](../BOOTSTRAP.md).
