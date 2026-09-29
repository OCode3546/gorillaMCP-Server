# Agent: Code & Errors Helper — MCP Compatible

**Purpose:** Focused debugging and code error resolution. Helps understand, fix, and verify code issues with clear, minimal changes. Specializes in compiler errors, runtime issues, stack traces, failing tests, and code snippets.

**Capabilities:**
- Analyze compiler and runtime errors
- Review and explain stack traces
- Debug failing tests
- Fix code issues with minimal changes
- Verify fixes with tests or reproduction
- Explain error root causes
- Suggest targeted fixes

**Constraints:**
- Does not guess at root causes without evidence
- Prefers small, targeted fixes over broad rewrites
- Requires error messages, stack traces, or failing code
- Verifies fixes with tests or available evidence
- Explains what changed and why

**Entrypoint:** `run_agent.py` with `run(task: dict) -> dict` function

**Task Schema:**
```json
{
  "goal": "Fix the TypeError in user authentication",
  "targets": ["src/auth/", "tests/auth/"],
  "error_message": "TypeError: 'NoneType' object is not subscriptable",
  "stack_trace": "...",
  "code_snippet": "...",
  "test_command": "pytest tests/auth/",
  "reproduce_steps": [...],
  "expected_behavior": "..."
}
```

**Returns:**
- Status (success/failed)
- Diagnosis of the problem
- Root cause explanation
- Recommended fix
- Verification results
- Risks and next actions
- Optional: patch file with fix
