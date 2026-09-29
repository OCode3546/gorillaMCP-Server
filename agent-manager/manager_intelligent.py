#!/usr/bin/env python3
"""
Enhanced Agent Manager with Intelligent Task Routing

This manager reads the taskfile.json configuration and intelligently routes user tasks
to the appropriate agent. It works like a real manager: takes requests, analyzes them,
assigns to the right "employee" (agent), and tracks execution.

Usage:
  python manager_intelligent.py task "user prompt describing what they need"
  python manager_intelligent.py task "Implement a login form" --agent agent-builder
  python manager_intelligent.py list-agents
  python manager_intelligent.py show-categories
"""

import argparse
import importlib.util
import subprocess
import json
import os
import sys
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Agents live next to this folder, in the workspace root.
PROMPTS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGER_DIR = os.path.dirname(__file__)
TASKFILE_PATH = os.path.join(MANAGER_DIR, "taskfile.json")


def load_taskfile() -> Dict:
    """Load and parse the taskfile.json configuration."""
    if not os.path.exists(TASKFILE_PATH):
        return {}
    with open(TASKFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_agents() -> Dict[str, str]:
    """Discover agents in the prompts directory."""
    agents = {}
    if not os.path.isdir(PROMPTS_ROOT):
        return agents
    for name in os.listdir(PROMPTS_ROOT):
        folder = os.path.join(PROMPTS_ROOT, name)
        if os.path.isdir(folder):
            py_runner = os.path.join(folder, "run_agent.py")
            js_runner = os.path.join(folder, "run_agent.js")
            if os.path.exists(py_runner):
                agents[name] = py_runner
            elif os.path.exists(js_runner):
                agents[name] = js_runner
    return agents


def classify_task(user_prompt: str, taskfile: Dict) -> Tuple[str, Dict]:
    """
    Classify user task by analyzing keywords against routing rules.
    
    Returns:
        (category_name, category_definition)
    """
    prompt_lower = user_prompt.lower()
    routing_rules = taskfile.get("routing_rules", {}).get("priority_keywords", [])
    
    # Try to match against routing rules
    for rule in routing_rules:
        pattern = rule.get("pattern", "")
        if re.search(pattern, prompt_lower):
            category_name = rule.get("category", "")
            category_def = taskfile.get("task_classification", {}).get(category_name, {})
            return category_name, category_def
    
    # Default fallback
    default_category = "feature_development"
    category_def = taskfile.get("task_classification", {}).get(default_category, {})
    return default_category, category_def


def structure_task(user_prompt: str, category: str, taskfile: Dict) -> Dict:
    """
    Convert unstructured user prompt into a structured task JSON.
    """
    category_def = taskfile.get("task_classification", {}).get(category, {})
    template = category_def.get("task_template", {})
    
    # Create task based on template
    task = {
        "goal": user_prompt,
        "targets": template.get("targets", ["src/"]),
        "requirements": template.get("requirements", []),
        "depth": template.get("depth", "full"),
        "category": category,
        "user_prompt": user_prompt
    }
    
    return task


def print_manager_response(stage: str, content: Dict):
    """Print manager responses in a friendly format."""
    print("\n" + "=" * 70)
    print(f"[MANAGER] {stage}")
    print("=" * 70)
    print(json.dumps(content, indent=2))
    print()


def load_and_run(runner_path: str, task: Dict) -> Dict:
    """Execute agent runner (Python or JavaScript)."""
    if runner_path.endswith('.py'):
        spec = importlib.util.spec_from_file_location("run_agent", runner_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "run"):
            return {"status": "failed", "summary": "Runner missing run(task)"}
        return module.run(task)
    elif runner_path.endswith('.js'):
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


def display_task_categories(taskfile: Dict):
    """Display all available task categories."""
    categories = taskfile.get("task_classification", {})
    print("\n" + "=" * 70)
    print("AVAILABLE TASK CATEGORIES")
    print("=" * 70)
    for cat_name, cat_def in categories.items():
        print(f"\n📋 {cat_def.get('name', cat_name)}")
        print(f"   Category: {cat_name}")
        print(f"   Description: {cat_def.get('description', 'N/A')}")
        print(f"   Assigned to: {cat_def.get('assigned_to', 'N/A')}")
        keywords = cat_def.get('keywords', [])
        if keywords:
            print(f"   Keywords: {', '.join(keywords)}")


def display_agents(agents: Dict, taskfile: Dict):
    """Display available agents."""
    print("\n" + "=" * 70)
    print("AVAILABLE AGENTS")
    print("=" * 70)
    agents_config = taskfile.get("agents", {})
    
    for agent_name, agent_path in agents.items():
        agent_info = agents_config.get(agent_name, {})
        print(f"\n🤖 {agent_info.get('name', agent_name)}")
        print(f"   Agent ID: {agent_name}")
        print(f"   Role: {agent_info.get('role', 'N/A')}")
        print(f"   Description: {agent_info.get('description', 'N/A')}")
        capabilities = agent_info.get('capabilities', [])
        if capabilities:
            print(f"   Capabilities: {', '.join(capabilities)}")
        print(f"   Runner: {agent_path}")


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Intelligent Agent Manager - Routes tasks to appropriate agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manager_intelligent.py task "Implement a login form"
  python manager_intelligent.py task "Fix bug in payment processing"
  python manager_intelligent.py list-agents
  python manager_intelligent.py show-categories
        """)
    
    p.add_argument("command", choices=["task", "list-agents", "show-categories"], 
                   help="Action to perform")
    p.add_argument("prompt", nargs="?", help="User task prompt (for 'task' command)")
    p.add_argument("--agent", help="Override agent assignment (optional)")
    p.add_argument("--skip-approval", action="store_true", 
                   help="Skip confirmation and run immediately")
    
    args = p.parse_args(argv)
    
    # Load configuration
    taskfile = load_taskfile()
    if not taskfile:
        print("ERROR: taskfile.json not found or invalid")
        return 1
    
    agents = find_agents()
    
    if args.command == "list-agents":
        display_agents(agents, taskfile)
        return 0
    
    if args.command == "show-categories":
        display_task_categories(taskfile)
        return 0
    
    if args.command == "task":
        if not args.prompt:
            print("ERROR: Task prompt required")
            return 2
        
        # Step 1: Analyze task
        print("\n" + "=" * 70)
        print("[MANAGER] Received task request. Analyzing...")
        print("=" * 70)
        
        category, category_def = classify_task(args.prompt, taskfile)
        print(f"\n✓ Task classified as: {category_def.get('name', category)}")
        
        # Step 2: Assign agent
        assigned_agent = args.agent or category_def.get("assigned_to", "agent-builder")
        
        if assigned_agent not in agents:
            print(f"ERROR: Agent '{assigned_agent}' not found")
            return 2
        
        agent_info = taskfile.get("agents", {}).get(assigned_agent, {})
        print(f"✓ Assigned to: {agent_info.get('name', assigned_agent)}")
        print(f"  Role: {agent_info.get('role', 'Specialist')}")
        
        # Step 3: Structure task
        task = structure_task(args.prompt, category, taskfile)
        
        print_manager_response("TASK PLAN", {
            "goal": task.get("goal"),
            "targets": task.get("targets"),
            "requirements": task.get("requirements"),
            "depth": task.get("depth")
        })
        
        # Step 4: Get approval
        if not args.skip_approval:
            response = input("[MANAGER] Proceed with task execution? [y/n]: ").strip().lower()
            if response != 'y':
                print("[MANAGER] Task cancelled.")
                return 0
        
        # Step 5: Execute task
        print(f"\n[MANAGER] Delegating to {agent_info.get('name', assigned_agent)}...")
        result = load_and_run(agents[assigned_agent], task)
        
        # Step 6: Report results
        print_manager_response("EXECUTION RESULT", result)
        
        # Summary
        status = result.get("status", "unknown")
        summary = result.get("summary", "No summary provided")
        artifacts = result.get("artifacts", [])
        
        print("=" * 70)
        print("[MANAGER] FINAL REPORT")
        print("=" * 70)
        print(f"Status: {status}")
        print(f"Summary: {summary}")
        if artifacts:
            print(f"Artifacts Generated:")
            for artifact in artifacts:
                print(f"  - {artifact}")
        print("=" * 70 + "\n")
        
        return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
