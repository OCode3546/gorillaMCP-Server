


"""Simple local agent manager.

Usage:
  python manager.py list
  python manager.py run --agent agent-builder --task-json '{"goal":"...","targets":["src/"]}'

The manager discovers agents in the prompts directory. Each agent must expose `run_agent.py` with a `run(task: dict) -> dict` function.
"""
import argparse
import importlib.util
import subprocess
import json
import os
import sys
from typing import Dict

# Agents live next to this folder, in the workspace root.
PROMPTS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_agents() -> Dict[str, str]:
    agents = {}
    if not os.path.isdir(PROMPTS_ROOT):
        return agents
    for name in os.listdir(PROMPTS_ROOT):
        folder = os.path.join(PROMPTS_ROOT, name)
        if os.path.isdir(folder):
            # Prefer Python runner, fall back to Node runner
            py_runner = os.path.join(folder, "run_agent.py")
            js_runner = os.path.join(folder, "run_agent.js")
            if os.path.exists(py_runner):
                agents[name] = py_runner
            elif os.path.exists(js_runner):
                agents[name] = js_runner
    return agents


def load_and_run(runner_path: str, task: Dict) -> Dict:
    if runner_path.endswith('.py'):
        spec = importlib.util.spec_from_file_location("run_agent", runner_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "run"):
            return {"status": "failed", "summary": "Runner missing run(task)"}
        return module.run(task)
    elif runner_path.endswith('.js'):
        # Invoke Node runner via subprocess
        cmd = ["node", runner_path, "--task-json", json.dumps(task)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            out = proc.stdout.strip()
            if not out:
                return {"status": "failed", "summary": "Runner produced no output", "stderr": proc.stderr}
            return json.loads(out)
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "summary": "Node runner failed", "stderr": e.stderr}
        except Exception as e:
            return {"status": "failed", "summary": f"Failed to run node runner: {e}"}
    else:
        return {"status": "failed", "summary": "Unsupported runner type"}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["list", "run"], help="Action")
    p.add_argument("--agent", help="Agent folder name")
    p.add_argument("--task-file", help="Task JSON file")
    p.add_argument("--task-json", help="Task JSON string")
    args = p.parse_args(argv)

    agents = find_agents()
    if args.command == "list":
        if not agents:
            print("No agents found in prompts folder.")
            return 0
        for name, runner in agents.items():
            print(f"- {name}: {runner}")
        return 0

    if args.command == "run":
        if not args.agent:
            print("--agent is required for run")
            return 2
        if args.agent not in agents:
            print(f"Agent '{args.agent}' not found")
            return 2
        if args.task_file:
            raw = open(args.task_file, "r", encoding="utf-8").read()
        elif args.task_json:
            raw = args.task_json
        else:
            print("Provide --task-file or --task-json")
            return 2
        task = json.loads(raw)
        print(f"Running agent {args.agent}...")
        result = load_and_run(agents[args.agent], task)
        print(json.dumps(result, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
