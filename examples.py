#!/usr/bin/env python3
"""
Example usage of the new agents.
Shows practical real-world scenarios for both file-sorter and code-errors agents.

Run these examples to see how the agents work in practice.
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent


def example_file_sorter_organize():
    """Example 1: Organize project files by type."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Organize Project Files by Type")
    print("=" * 70)
    
    print("\nScenario: New developer joins project, wants to understand structure")
    
    file_sorter_path = WORKSPACE_ROOT / "file-sorter-agent" / "run_agent.py"
    
    task = {
        "goal": "Analyze and organize project files by type",
        "targets": ["agent-builder/", "agent-manager/", "fastmcp/"],
        "sort_by": "type"
    }
    
    print(f"\nTask:\n{json.dumps(task, indent=2)}")
    
    result = subprocess.run(
        [sys.executable, str(file_sorter_path), "--task-json", json.dumps(task)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(WORKSPACE_ROOT)
    )
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"\nResult Status: {output.get('status')}")
        print(f"Summary: {output.get('summary')}")
        print(f"\nFile Breakdown:")
        for category, count in output.get('groups', {}).items():
            print(f"  - {category:15} {count:3} files")
        
        if output.get('report'):
            print("\nReport Preview (first 500 chars):")
            print(output.get('report')[:500] + "...")
    else:
        print(f"Error: {result.stderr}")


def example_file_sorter_size():
    """Example 2: Find large files taking up space."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Find Large Files (Storage Analysis)")
    print("=" * 70)
    
    print("\nScenario: Need to clean up disk space, find what's using it")
    
    file_sorter_path = WORKSPACE_ROOT / "file-sorter-agent" / "run_agent.py"
    
    task = {
        "goal": "Identify large files for storage optimization",
        "targets": ["."],
        "sort_by": "size"
    }
    
    print(f"\nTask:\n{json.dumps(task, indent=2)}")
    
    result = subprocess.run(
        [sys.executable, str(file_sorter_path), "--task-json", json.dumps(task)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(WORKSPACE_ROOT)
    )
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"\nResult Status: {output.get('status')}")
        print(f"Total Files: {output.get('files_found')}")
        print(f"Total Size: {output.get('total_size_mb')} MB")
        print(f"\nSize Categories:")
        for category, count in output.get('groups', {}).items():
            print(f"  - {category:15} {count:3} files")
        
        print("\nFolders Suggestion (first 10):")
        for suggestion in output.get('suggestions', [])[:10]:
            if suggestion.startswith('mkdir'):
                print(f"  {suggestion}")
    else:
        print(f"Error: {result.stderr}")


def example_code_errors_typeerror():
    """Example 3: Fix a TypeError."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Debug and Fix a TypeError")
    print("=" * 70)
    
    print("\nScenario: TypeError in production, need quick diagnosis")
    
    code_errors_path = WORKSPACE_ROOT / "code-errors-agent" / "run_agent.py"
    
    task = {
        "goal": "Fix TypeError in payment processing",
        "error_message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "code_snippet": "def calculate_total(amount, tip):\n    return amount + tip  # tip might be string from form",
        "expected_behavior": "Should convert tip to int before adding",
        "test_command": "pytest tests/test_payment.py::test_calculate_total"
    }
    
    print(f"\nTask:\n{json.dumps(task, indent=2)}")
    
    result = subprocess.run(
        [sys.executable, str(code_errors_path), "--task-json", json.dumps(task)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"\nResult Status: {output.get('status')}")
        print(f"Error Type: {output.get('error_type')}")
        print(f"Summary: {output.get('summary')}")
        
        print("\nSuggested Fixes:")
        for i, suggestion in enumerate(output.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
        
        print("\nDiagnosis (preview):")
        diagnosis = output.get('diagnosis', '')
        lines = diagnosis.split('\n')[:10]
        for line in lines:
            print(f"  {line}")
    else:
        print(f"Error: {result.stderr}")


def example_code_errors_attribute():
    """Example 4: Fix an AttributeError."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Debug and Fix an AttributeError")
    print("=" * 70)
    
    print("\nScenario: AttributeError in user profile, need to add None check")
    
    code_errors_path = WORKSPACE_ROOT / "code-errors-agent" / "run_agent.py"
    
    task = {
        "goal": "Fix AttributeError in user profile endpoint",
        "error_message": "AttributeError: 'NoneType' object has no attribute 'email'",
        "stack_trace": 'File "routes/user.py", line 42, in get_profile\n  return user.email',
        "code_snippet": "def get_profile(user_id):\n    user = db.query(User).filter(id=user_id).first()\n    return {\"email\": user.email}  # Crashes if user is None",
        "reproduce_steps": [
            "Call GET /api/user/999 with non-existent user",
            "Observe AttributeError"
        ],
        "expected_behavior": "Should return 404 Not Found, not crash"
    }
    
    print(f"\nTask:\n{json.dumps(task, indent=2)}")
    
    result = subprocess.run(
        [sys.executable, str(code_errors_path), "--task-json", json.dumps(task)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"\nResult Status: {output.get('status')}")
        print(f"Error Type: {output.get('error_type')}")
        print(f"Location: {output.get('location')}")
        
        print("\nSuggested Fixes:")
        for i, suggestion in enumerate(output.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
        
        print("\nDiagnosis Preview:")
        diagnosis = output.get('diagnosis', '')
        lines = diagnosis.split('\n')[:15]
        for line in lines:
            print(f"  {line}")
    else:
        print(f"Error: {result.stderr}")


def example_code_errors_zero_division():
    """Example 5: Fix a ZeroDivisionError."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Debug and Fix a ZeroDivisionError")
    print("=" * 70)
    
    print("\nScenario: Division by zero in discount calculation")
    
    code_errors_path = WORKSPACE_ROOT / "code-errors-agent" / "run_agent.py"
    
    task = {
        "goal": "Fix ZeroDivisionError in discount calculation",
        "error_message": "ZeroDivisionError: float division by zero",
        "code_snippet": "def calculate_discount(original_price, discounted_price):\n    # Calculate discount percentage\n    discount_rate = (original_price - discounted_price) / original_price\n    return discount_rate * 100",
        "reproduce_steps": [
            "Calculate discount with original_price = 0",
            "Get ZeroDivisionError"
        ],
        "expected_behavior": "Should handle zero or invalid prices gracefully"
    }
    
    print(f"\nTask:\n{json.dumps(task, indent=2)}")
    
    result = subprocess.run(
        [sys.executable, str(code_errors_path), "--task-json", json.dumps(task)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"\nResult Status: {output.get('status')}")
        print(f"Error Type: {output.get('error_type')}")
        
        print("\nSuggested Fixes:")
        for i, suggestion in enumerate(output.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
        
        print(f"\nDiagnostic Report Generated: {bool(output.get('artifacts'))}")
        if output.get('artifacts'):
            print(f"  Artifact: {output.get('artifacts')[0]}")
    else:
        print(f"Error: {result.stderr}")


def main():
    """Run all examples."""
    print("\n🎯 Agent Usage Examples")
    print("=" * 70)
    print("\nThese examples demonstrate real-world use cases for both agents")
    
    examples = [
        ("File Sorter: Organize by Type", example_file_sorter_organize),
        ("File Sorter: Find Large Files", example_file_sorter_size),
        ("Code Errors: Fix TypeError", example_code_errors_typeerror),
        ("Code Errors: Fix AttributeError", example_code_errors_attribute),
        ("Code Errors: Fix ZeroDivisionError", example_code_errors_zero_division),
    ]
    
    if len(sys.argv) > 1:
        # Run specific example
        example_num = int(sys.argv[1]) - 1
        if 0 <= example_num < len(examples):
            title, func = examples[example_num]
            print(f"\nRunning: {title}")
            func()
        else:
            print(f"Example {example_num + 1} not found")
    else:
        # Run all examples
        for i, (title, func) in enumerate(examples, 1):
            print(f"\n[{i}/{len(examples)}] Running: {title}")
            try:
                func()
            except Exception as e:
                print(f"Error: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Examples complete!")
    print("\nTo run a specific example:")
    print("  python examples.py 1  # First example")
    print("  python examples.py 2  # Second example")
    print("  etc.")


if __name__ == "__main__":
    main()
