# Agent: Builder Agent — manager-compatible

Purpose:
Metadata and entrypoint for the workspace-scoped Builder Agent skill. This file explains how `agent-manager/manager.py` can discover and run this agent.

Entrypoint:

- `run_agent.py` (must expose a `run(task: dict) -> dict` function and a CLI that accepts JSON input).

Capabilities:

- Implements the `Builder Agent` SKILL.md workflow: planning, patch creation, and checks.
- Exposes a lightweight runner that can be invoked by an orchestrator.

Location:
This file lives next to `SKILL.md` and `run_agent.py` in the same folder.
