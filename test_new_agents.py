#!/usr/bin/env python3
"""
Quick test script for the new agents.
Tests both file-sorter-agent and code-errors-agent.

Usage:
  python test_new_agents.py                    # Run all tests
  python test_new_agents.py file-sorter        # Test file sorter only
  python test_new_agents.py code-errors        # Test code errors only
"""

import json
import subprocess
import sys
from pathlib import Path

# Get the workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent


def run_file_sorter_test():
    """Test the file sorter agent."""
    print("\n" + "=" * 70)
    print("Testing File Sorter Agent")
    print("=" * 70)
    
    file_sorter_path = WORKSPACE_ROOT / "file-sorter-agent" / "run_agent.py"
    
    if not file_sorter_path.exists():
        print("❌ File sorter agent not found!")
        return False
    
    print(f"✓ Found file sorter at {file_sorter_path}")
    
    # Test 1: Sort by type
    print("\nTest 1: Sort files by type")
    task1 = {
        "goal": "Organize workspace files by type",
        "targets": ["."],
        "sort_by": "type"
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(file_sorter_path), "--task-json", json.dumps(task1)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(WORKSPACE_ROOT)
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(f"✓ Status: {output.get('status')}")
            print(f"✓ Files found: {output.get('files_found')}")
            print(f"✓ Total size: {output.get('total_size_mb')} MB")
            print(f"✓ Categories: {', '.join(output.get('groups', {}).keys())}")
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Sort by size
    print("\nTest 2: Sort files by size")
    task2 = {
        "goal": "Find largest files",
        "targets": ["."],
        "sort_by": "size"
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(file_sorter_path), "--task-json", json.dumps(task2)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(WORKSPACE_ROOT)
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(f"✓ Status: {output.get('status')}")
            print(f"✓ Grouped by size: {', '.join(output.get('groups', {}).keys())}")
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✓ File Sorter Agent: All tests passed!")
    return True


def run_code_errors_test():
    """Test the code errors agent."""
    print("\n" + "=" * 70)
    print("Testing Code & Errors Helper Agent")
    print("=" * 70)
    
    code_errors_path = WORKSPACE_ROOT / "code-errors-agent" / "run_agent.py"
    
    if not code_errors_path.exists():
        print("❌ Code errors agent not found!")
        return False
    
    print(f"✓ Found code errors agent at {code_errors_path}")
    
    # Test 1: Analyze TypeError
    print("\nTest 1: Analyze TypeError")
    task1 = {
        "goal": "Fix TypeError",
        "error_message": "TypeError: 'NoneType' object is not subscriptable",
        "code_snippet": "user = db.get_user(id)\nname = user['name']"
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(code_errors_path), "--task-json", json.dumps(task1)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(f"✓ Status: {output.get('status')}")
            print(f"✓ Error type: {output.get('error_type')}")
            print(f"✓ Suggestions: {len(output.get('suggestions', []))} fix suggestions")
            if output.get('suggestions'):
                for i, suggestion in enumerate(output.get('suggestions', [])[:3], 1):
                    print(f"  {i}. {suggestion}")
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Analyze AttributeError
    print("\nTest 2: Analyze AttributeError")
    task2 = {
        "goal": "Fix AttributeError",
        "error_message": "AttributeError: 'NoneType' object has no attribute 'email'",
        "stack_trace": 'File "app.py", line 42, in get_profile\nreturn user.email',
        "code_snippet": "def get_profile(user_id):\n  user = db.query(User).first()\n  return user.email"
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(code_errors_path), "--task-json", json.dumps(task2)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(f"✓ Status: {output.get('status')}")
            print(f"✓ Error type: {output.get('error_type')}")
            print(f"✓ Location: {output.get('location')}")
            print(f"✓ Diagnosis provided: {bool(output.get('diagnosis'))}")
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Analyze ZeroDivisionError
    print("\nTest 3: Analyze ZeroDivisionError")
    task3 = {
        "goal": "Fix ZeroDivisionError",
        "error_message": "ZeroDivisionError: float division by zero",
        "code_snippet": "discount_rate = total_discount / subtotal"
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(code_errors_path), "--task-json", json.dumps(task3)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(f"✓ Status: {output.get('status')}")
            print(f"✓ Error type: {output.get('error_type')}")
            print(f"✓ Artifact generated: {bool(output.get('artifacts'))}")
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✓ Code Errors Agent: All tests passed!")
    return True


def main():
    """Run tests."""
    print("\n🧪 Testing New Agents")
    print("=" * 70)
    
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    results = {}
    
    if test_type in ["all", "file-sorter"]:
        results["file-sorter"] = run_file_sorter_test()
    
    if test_type in ["all", "code-errors"]:
        results["code-errors"] = run_code_errors_test()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for agent, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{agent:20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())




# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.