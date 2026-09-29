Builder Agent — Runner instructions (for `agent-manager`)

Purpose
This document specifies the minimal runner interface that an agent must provide so that `agent-manager/manager.py` can discover and invoke it.

Required interface
- File: `run_agent.py`
- Callable: `def run(task: dict) -> dict` — accepts a task dictionary and returns a result dict with keys: `status` (success|failed), `summary`, and optional `artifacts` list.
- CLI: `python run_agent.py --task-file /path/to/task.json` or `--task-json '{...}'` which will call `run()` and print a JSON result to stdout.

Behavior
- Validate inputs and produce a short plan before making any filesystem changes.
- If making edits, write patch files to a safe output folder (e.g., `outgoing_patches/`) and return their paths in `artifacts`.
- Do not perform destructive operations without explicit confirmation from `agent-manager` or the user.

Example result format
{
  "status": "success",
  "summary": "Added unit tests and fixed lint issues.",
  "artifacts": ["outgoing_patches/0001-fix-auth.patch"]
}

Security
- Never log or return secrets.
- Limit the scope of edits to the target folder unless explicitly authorized.
