"""Code & Errors Helper Agent - Debugging and error resolution.

This agent helps understand, fix, and verify code issues with clear,
minimal changes. It focuses on compiler errors, runtime issues, stack traces,
failing tests, and code problem analysis.

Exposes `run(task: dict) -> dict` function for MCP integration.
"""

import json
import os
import sys
import uuid
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "outgoing_patches")
os.makedirs(OUT_DIR, exist_ok=True)


def extract_error_info(error_message: str) -> Dict[str, Any]:
    """Extract structured information from error messages."""
    info = {
        "error_type": None,
        "error_message": error_message,
        "likely_cause": None,
        "common_fixes": [],
    }
    
    # Identify error type
    error_patterns = {
        r"TypeError": ("TypeError", ["Check variable types", "Verify argument types", "Check for None values"]),
        r"AttributeError": ("AttributeError", ["Check attribute exists", "Verify object initialization", "Check for None"]),
        r"NameError": ("NameError", ["Check variable is defined", "Check for typos", "Check scope"]),
        r"IndexError": ("IndexError", ["Check index bounds", "Verify list/array length", "Check for empty collections"]),
        r"KeyError": ("KeyError", ["Check dictionary key exists", "Use .get() with default", "Verify key name"]),
        r"ValueError": ("ValueError", ["Check argument values", "Validate input format", "Check conversion errors"]),
        r"FileNotFoundError": ("FileNotFoundError", ["Check file path", "Verify file exists", "Check working directory"]),
        r"ZeroDivisionError": ("ZeroDivisionError", ["Add zero check before division", "Validate denominators"]),
        r"SyntaxError": ("SyntaxError", ["Check syntax", "Look for missing brackets", "Check indentation"]),
        r"ImportError": ("ImportError", ["Check module path", "Verify installation", "Check imports"]),
    }
    
    for pattern, (error_type, fixes) in error_patterns.items():
        if re.search(pattern, error_message, re.IGNORECASE):
            info["error_type"] = error_type
            info["common_fixes"] = fixes
            break
    
    return info


def analyze_stack_trace(stack_trace: str) -> Dict[str, Any]:
    """Analyze a stack trace to identify the problematic code."""
    analysis = {
        "file": None,
        "line_number": None,
        "function": None,
        "context": [],
        "depth": len(stack_trace.split("\n")),
    }
    
    # Extract file and line info
    file_pattern = r'File "([^"]+)", line (\d+)(?:, in (.+))?'
    matches = re.findall(file_pattern, stack_trace)
    
    if matches:
        # Get the most recent (last) file in trace
        last_match = matches[-1]
        analysis["file"] = last_match[0]
        analysis["line_number"] = int(last_match[1])
        analysis["function"] = last_match[2] if len(last_match) > 2 else None
    
    # Extract context lines
    context_pattern = r'(\s+.+)'
    context_matches = re.findall(context_pattern, stack_trace)
    analysis["context"] = context_matches[:5]  # First 5 context lines
    
    return analysis


def create_diagnosis(task: Dict[str, Any], error_info: Dict, trace_analysis: Dict) -> str:
    """Create a diagnostic summary of the issue."""
    diagnosis_lines = [
        "## DIAGNOSIS",
        "",
        f"**Error Type:** {error_info.get('error_type', 'Unknown')}",
        f"**Error Message:** {task.get('error_message', 'Not provided')}",
        "",
    ]
    
    if trace_analysis.get("file"):
        diagnosis_lines.append(f"**Location:** {trace_analysis['file']}:{trace_analysis.get('line_number', '?')}")
        if trace_analysis.get("function"):
            diagnosis_lines.append(f"**Function:** {trace_analysis['function']}")
    
    diagnosis_lines.extend([
        "",
        "## ROOT CAUSE ANALYSIS",
        "",
        "Based on the error type and available context, likely causes:",
    ])
    
    for i, fix in enumerate(error_info.get("common_fixes", []), 1):
        diagnosis_lines.append(f"{i}. {fix}")
    
    return "\n".join(diagnosis_lines)


def create_fix_suggestions(error_info: Dict, code_snippet: Optional[str]) -> List[str]:
    """Generate fix suggestions based on error type."""
    suggestions = []
    error_type = error_info.get("error_type")
    
    fix_templates = {
        "TypeError": [
            "Add type checking before operations",
            "Use isinstance() to verify types",
            "Check for None before accessing attributes",
            "Use try/except for type conversions",
        ],
        "AttributeError": [
            "Verify object is initialized",
            "Check attribute name spelling",
            "Add hasattr() check before access",
            "Initialize missing attributes in __init__",
        ],
        "NameError": [
            "Define variable before use",
            "Check for typos in variable names",
            "Import required modules",
            "Check variable scope",
        ],
        "IndexError": [
            "Add bounds checking",
            "Use try/except for index access",
            "Check list length before indexing",
            "Use .get() for dictionary access",
        ],
        "KeyError": [
            "Check key exists before access",
            "Use dict.get(key, default)",
            "Verify dictionary is populated",
            "Use .setdefault() for missing keys",
        ],
        "ZeroDivisionError": [
            "Add denominator check before division",
            "Handle zero case separately",
            "Use try/except for division",
            "Validate divisor is non-zero",
        ],
    }
    
    if error_type in fix_templates:
        suggestions.extend(fix_templates[error_type])
    else:
        suggestions = [
            "Review error message carefully",
            "Check documentation for this error",
            "Search Stack Overflow for similar issues",
            "Add debugging print statements",
        ]
    
    return suggestions


def run_verification(test_command: Optional[str]) -> Optional[Dict[str, Any]]:
    """Run test/verification command if provided."""
    if not test_command:
        return None
    
    try:
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        return {
            "command": test_command,
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout[:500],  # First 500 chars
            "stderr": result.stderr[:500],
        }
    except Exception as e:
        return {
            "command": test_command,
            "error": str(e),
            "passed": False,
        }


def create_patch(content: str) -> str:
    """Create a patch file with diagnostic and fix info."""
    name = f"code-fix-{uuid.uuid4().hex[:8]}.patch"
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def run(task: Dict[str, Any]) -> Dict[str, Any]:
    """Main execution function for MCP integration."""
    goal = task.get("goal", "Debug code issue")
    error_message = task.get("error_message", "")
    stack_trace = task.get("stack_trace", "")
    code_snippet = task.get("code_snippet", "")
    test_command = task.get("test_command")
    reproduce_steps = task.get("reproduce_steps", [])
    expected_behavior = task.get("expected_behavior", "")
    
    # Validate we have enough info
    if not error_message and not stack_trace and not code_snippet:
        return {
            "status": "failed",
            "summary": "Insufficient information to diagnose issue",
            "plan": "Please provide: error_message, stack_trace, and/or code_snippet",
            "diagnosis": "No error information provided",
        }
    
    # Analyze error information
    error_info = extract_error_info(error_message)
    trace_analysis = analyze_stack_trace(stack_trace) if stack_trace else {}
    
    # Create diagnosis
    diagnosis = create_diagnosis(task, error_info, trace_analysis)
    
    # Generate fix suggestions
    suggestions = create_fix_suggestions(error_info, code_snippet)
    
    # Run verification if test provided
    verification = run_verification(test_command)
    
    # Build plan
    plan_lines = [
        f"1. Identified error type: {error_info.get('error_type', 'Unknown')}",
        f"2. Located issue at: {trace_analysis.get('file', 'Unknown file')}:{trace_analysis.get('line_number', '?')}",
        "3. Analyzed root causes",
        "4. Generated fix suggestions",
        "5. Ready for targeted fix implementation",
    ]
    
    if test_command:
        plan_lines.append("6. Verification test prepared")
    
    plan = "\n".join(plan_lines)
    
    # Create patch with diagnostic info
    patch_content = f"""# Code Error Diagnostic Report

## ISSUE SUMMARY
Goal: {goal}

{diagnosis}

## SUGGESTED FIXES
{chr(10).join(f"- {s}" for s in suggestions)}

## CODE SNIPPET
```
{code_snippet}
```

## EXPECTED BEHAVIOR
{expected_behavior}

## REPRODUCTION STEPS
{chr(10).join(f"- {step}" for step in reproduce_steps) if reproduce_steps else "None provided"}

## NEXT ACTIONS
1. Review the suggested fixes above
2. Apply the most relevant fix to your code
3. Run the test/verification command
4. Verify the fix resolves the issue
"""
    
    patch_path = create_patch(patch_content)
    
    return {
        "status": "success",
        "summary": f"Diagnosed {error_info.get('error_type', 'unknown')} error and generated fix suggestions",
        "plan": plan,
        "diagnosis": diagnosis,
        "error_type": error_info.get("error_type"),
        "location": f"{trace_analysis.get('file', '?')}:{trace_analysis.get('line_number', '?')}",
        "suggestions": suggestions,
        "verification": verification,
        "artifacts": [patch_path],
    }


def _cli_main():
    """CLI entry point for direct execution."""
    import argparse
    
    p = argparse.ArgumentParser(description="Run Code Errors Agent task")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-file", help="Path to JSON task file")
    group.add_argument("--task-json", help="Task JSON string")
    args = p.parse_args()
    
    if args.task_file:
        raw = open(args.task_file, "r", encoding="utf-8").read()
    else:
        raw = args.task_json
    
    task = json.loads(raw)
    result = run(task)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli_main()
