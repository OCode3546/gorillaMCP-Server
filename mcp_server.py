from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

PROMPTS_ROOT = Path(__file__).resolve().parent

mcp = FastMCP(
    "Workspace Agent Registry",
    instructions=(
        "Expose the local agent folders in this workspace as MCP tools. "
        "Agents can be listed, inspected, and invoked with goal-driven tasks. "
        "Use stdio for local clients and streamable HTTP for remote deployment."
    ),
)


def discover_agents(base_dir: str | Path | None = None) -> list[dict[str, Any]]:
    root = Path(base_dir) if base_dir is not None else PROMPTS_ROOT
    agents: list[dict[str, Any]] = []
    if not root.exists():
        return agents

    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue

        runner = None
        if (child / "run_agent.py").exists():
            runner = child / "run_agent.py"
            runner_type = "python"
        elif (child / "run_agent.js").exists():
            runner = child / "run_agent.js"
            runner_type = "node"
        else:
            continue

        description = "Workspace agent"
        for filename in ("AGENT.md", "README.md", "SKILL.md"):
            candidate = child / filename
            if candidate.exists():
                try:
                    text = candidate.read_text(encoding="utf-8")
                except OSError:
                    continue
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                for line in lines:
                    if not line.startswith("#") and line:
                        description = line[:180]
                        break
                break

        agents.append(
            {
                "name": child.name,
                "path": str(runner),
                "runner_type": runner_type,
                "description": description,
            }
        )
    return agents


def _agent_by_name(agent_name: str) -> dict[str, Any]:
    for agent in discover_agents():
        if agent["name"] == agent_name:
            return agent
    raise ValueError(f"Agent '{agent_name}' not found")


def _run_python_runner(runner_path: Path, task: dict[str, Any]) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(f"agent_runner_{runner_path.stem}", runner_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load runner module from {runner_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise ValueError(f"Runner {runner_path} is missing a run(task) function")
    return module.run(task)


def _run_node_runner(runner_path: Path, task: dict[str, Any]) -> dict[str, Any]:
    command = ["node", str(runner_path), "--task-json", json.dumps(task)]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=str(runner_path.parent))
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "Node runner failed"
        raise RuntimeError(stderr)

    output = completed.stdout.strip()
    if not output:
        raise RuntimeError(f"Runner {runner_path} produced no output")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Runner {runner_path} returned invalid JSON: {output}") from exc


def invoke_agent(agent_name: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
    if task is None:
        task = {}

    agent = _agent_by_name(agent_name)
    runner_path = Path(agent["path"])

    if agent["runner_type"] == "python":
        result = _run_python_runner(runner_path, task)
    elif agent["runner_type"] == "node":
        result = _run_node_runner(runner_path, task)
    else:
        raise ValueError(f"Unsupported runner type for agent '{agent_name}'")

    if not isinstance(result, dict):
        raise TypeError(f"Agent '{agent_name}' returned a non-dictionary result: {type(result)!r}")
    result.setdefault("agent", agent_name)
    return result


def orchestrate_agents(agent_names: list[str], task: dict[str, Any] | None = None) -> dict[str, Any]:
    if task is None:
        task = {}
    if not agent_names:
        return {
            "status": "failed",
            "summary": "No agents selected for orchestration",
            "agents": [],
            "results": [],
            "failed_agents": [],
        }

    results: list[dict[str, Any]] = []
    for agent_name in agent_names:
        try:
            # Each agent gets its own copy so one runner can't mutate the task for the next.
            result = invoke_agent(agent_name, dict(task))
        except Exception as exc:  # pragma: no cover - defensive branch
            result = {"status": "failed", "agent": agent_name, "summary": str(exc)}
        results.append(result)

    failed = [item.get("agent", "unknown") for item in results if item.get("status") == "failed"]
    if failed and len(failed) != len(results):
        status = "partial-success"
    elif failed:
        status = "failed"
    else:
        status = "success"

    return {
        "status": status,
        "summary": f"Orchestrated {len(agent_names)} agents; {len(results) - len(failed)} succeeded.",
        "agents": list(agent_names),
        "results": results,
        "failed_agents": failed,
    }


def build_server_manifest() -> dict[str, Any]:
    root = str(PROMPTS_ROOT)
    return {
        "name": "workspace-agent-registry",
        "version": "0.1.0",
        "description": "Exposes local workspace agents as MCP tools and supports orchestration across multiple agent runners.",
        "workspace_root": root,
        "transports": ["stdio", "streamable-http"],
        "entrypoint": {
            "command": sys.executable,
            "args": [str(PROMPTS_ROOT / "mcp_server.py"), "--transport", "stdio"],
        },
        "http": {
            "host": "127.0.0.1",
            "port": 8000,
            "path": "/mcp",
        },
        "features": {
            "offline_local": True,
            "multi_agent_orchestration": True,
            "resource_discovery": True,
            "prompt_templates": True,
        },
        "supported_tools": ["list_agents", "get_agent", "run_agent_tool", "orchestrate_agents_tool"],
    }


def _build_task(goal: str, targets: list[str] | None, extra: dict[str, Any] | None) -> dict[str, Any]:
    # MCP clients (e.g. Claude Desktop) may launch the server from any cwd, so
    # relative targets are anchored to the workspace root instead.
    resolved = [str((PROMPTS_ROOT / Path(t).expanduser()).resolve()) for t in (targets or [])]
    task: dict[str, Any] = {"goal": goal or "No goal provided", "targets": resolved}
    if extra:
        task.update(extra)
    return task


@mcp.tool
def list_agents() -> list[str]:
    """List all local agent folders in this workspace that expose a runnable entrypoint."""
    return [agent["name"] for agent in discover_agents()]


@mcp.tool
def get_agent(agent_name: str) -> dict[str, Any]:
    """Inspect the metadata for a named workspace agent."""
    return _agent_by_name(agent_name)


@mcp.tool
def run_agent_tool(agent_name: str, goal: str, targets: list[str] | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run an agent with a task objective and optional target paths (relative to the workspace root).

    Agent-specific fields go in `extra`:
    - agent-builder (code generator for web apps, APIs, desktop apps/executables, games, CLIs):
      mode ("plan" = dry run, the default; "generate" writes the project; "build" installs deps,
      runs tests and packages it; "templates" lists templates). Optional template (web-static,
      web-react, web-flask, api-fastapi, desktop-tkinter, desktop-electron, game-html5, game-pygame,
      cli-python; otherwise chosen from the goal), name, title, description, destination (exact
      project folder, absolute or ~), overwrite, build (build right after generate), project
      (folder for build mode). targets[0], if given, is the parent folder for the new project.
      After generating, customise the code for the goal before building.
    - code-errors-agent: needs at least one of error_message, stack_trace, code_snippet;
      optional test_command (a shell command run to verify), reproduce_steps, expected_behavior.
    - file-sorter-agent: mode ("plan" = dry run, the default; "apply" moves files; "undo" reverts
      the latest apply, or pass manifest=<id>; "history" lists applied runs). Optional sort_by
      ("type", "extension", "size", "date", "month", "year"), destination (absolute or ~ path),
      recursive, include/exclude globs, rules ([{"pattern"|"extensions"|"name_contains": ..., "folder": ...}]),
      categories, conflict ("rename", "skip", "overwrite"), copy, find_duplicates,
      duplicates_action ("report", "move"), remove_empty_dirs, force (required to apply inside a git repo).
      Always run a plan first and show it to the user before applying.
    """
    return invoke_agent(agent_name, _build_task(goal, targets, extra))


@mcp.tool
def orchestrate_agents_tool(agent_names: list[str], goal: str, targets: list[str] | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Route a single task to multiple workspace agents and aggregate the results."""
    return orchestrate_agents(agent_names, _build_task(goal, targets, extra))


@mcp.prompt
def agent_task_prompt(agent_name: str, goal: str, targets: list[str] | None = None) -> str:
    """Build a reusable prompt for instructing a workspace agent."""
    scope = ", ".join(targets) if targets else "the whole workspace"
    return (
        f"Run the {agent_name} agent to achieve: {goal}. "
        f"Limit work to {scope}. Return a concise plan and any patch artifacts that are generated."
    )


@mcp.resource("agent://index")
def agent_index_resource() -> str:
    """Expose the full agent index as a readable resource."""
    return json.dumps(discover_agents(), indent=2)


@mcp.resource("agent://{agent_name}")
def agent_resource(agent_name: str) -> str:
    """Expose one agent's metadata as a readable resource."""
    return json.dumps(_agent_by_name(agent_name), indent=2)


@mcp.resource("manifest://server")
def server_manifest_resource() -> str:
    """Expose the MCP server manifest for client configuration and discovery."""
    return json.dumps(build_server_manifest(), indent=2)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP server for local workspace agents")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport to use for clients",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    parser.add_argument("--print-manifest", action="store_true", help="Print the client manifest and exit")
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    if args.print_manifest:
        print(json.dumps(build_server_manifest(), indent=2))
        return

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()






# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.
