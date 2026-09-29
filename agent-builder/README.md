Builder Agent Skill — README

Overview
This workspace-scoped skill helps agents perform build/edit/review tasks for code, docs, configs, and tests. It provides a canonical workflow, decision points, and a Python template for common commands.

Where it lives
- Skill file: `agent-builder/SKILL.md`
- Examples: `agent-builder/EXAMPLES.md`

How to use
1. Invoke the skill with a concise goal, target files, and preferred depth (quick vs full).
2. Confirm any ambiguous decisions before the agent applies large or irreversible changes.
3. Ask the agent to run tests or linters if you want automated checks.

Customization
- Add language templates (TypeScript, Rust) by creating additional sections in `SKILL.md`.
- Provide repository-specific test and lint commands so the agent can run checks locally.

Next steps
- Add a TypeScript/Node template and a short commit/PR composition helper.
