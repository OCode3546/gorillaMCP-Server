# Code & Errors Helper Agent — Complete Guide

A specialized MCP agent for focused debugging and code error resolution. Analyzes compiler errors, runtime issues, stack traces, and failing tests to provide targeted fixes with minimal code changes.

## 🎯 What It Does

- **Analyzes errors**: Identifies error type and root cause
- **Parses stack traces**: Extracts file, line, and function information
- **Reviews code**: Examines snippets for issues
- **Generates fixes**: Provides targeted, minimal change suggestions
- **Verifies solutions**: Runs tests to confirm fixes work

## 🔍 Supported Error Types

The agent recognizes and analyzes:

| Error Type | Common Causes | Fixes Suggested |
|------------|---------------|-----------------|
| **TypeError** | Wrong type operations, None access | Type checks, isinstance() validation |
| **AttributeError** | Missing/typo attributes, None object | hasattr() checks, initialization |
| **NameError** | Undefined variables, typos | Define before use, check spelling |
| **IndexError** | Out of bounds access | Bounds checking, length verification |
| **KeyError** | Missing dictionary keys | Use .get(), check key exists |
| **ValueError** | Invalid argument values | Validate input, check format |
| **ZeroDivisionError** | Division by zero | Add denominator checks |
| **FileNotFoundError** | File doesn't exist | Verify path, check working dir |
| **ImportError** | Missing imports/modules | Check import paths, install deps |
| **SyntaxError** | Invalid Python syntax | Fix syntax, check indentation |

## 🚀 Quick Start

### Basic Usage

```bash
# Fix a TypeError
python ~/Library/Application\ Support/Code/User/prompts/code-errors-agent/run_agent.py \
  --task-json '{
    "goal": "Fix TypeError in user login",
    "error_message": "TypeError: '\''NoneType'\'' object is not subscriptable",
    "code_snippet": "user = db.query(User).filter(id=1).first()\nname = user['\''name'\'']",
    "test_command": "pytest tests/test_auth.py::test_login"
  }'
```

### Via MCP Server

```bash
# Using the MCP server
python mcp_server.py run_agent_tool code-errors-agent \
  "Fix the authentication bug" \
  --targets='["src/auth/"]' \
  --extra='{
    "error_message": "AttributeError: '\''NoneType'\'' object has no attribute '\''email'\''",
    "code_snippet": "user = authenticate(username)\nprint(user.email)"
  }'
```

## 📋 Task Schema

```json
{
  "goal": "Debug and fix the issue",
  "targets": ["src/auth/", "tests/"],
  "error_message": "TypeError: 'NoneType' object is not subscriptable",
  "stack_trace": "[Full stack trace]",
  "code_snippet": "[Problematic code]",
  "test_command": "pytest tests/test_auth.py",
  "reproduce_steps": [
    "Run python app.py",
    "Click login",
    "Enter invalid credentials"
  ],
  "expected_behavior": "Should show error message, not crash"
}
```

### Parameters

- **goal** (string, required): What needs to be fixed
- **targets** (list): Files/directories involved
- **error_message** (string): The error message from the error
- **stack_trace** (string): Full stack trace if available
- **code_snippet** (string): Problematic code section
- **test_command** (string): Command to verify fix (pytest, etc.)
- **reproduce_steps** (list): Steps to reproduce the issue
- **expected_behavior** (string): What should happen instead

## 💡 Use Cases

### 1. Fix TypeError from Error Message
```json
{
  "goal": "Fix TypeError in payment processing",
  "error_message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
  "code_snippet": "total = amount + tip",
  "test_command": "pytest tests/test_payment.py::test_calculate_total"
}
```

**Output:** Identifies type mismatch, suggests type conversion

### 2. Debug AttributeError from Stack Trace
```json
{
  "goal": "Fix AttributeError in user module",
  "stack_trace": "File 'user.py', line 42, in get_profile\nreturn user.email",
  "error_message": "AttributeError: 'NoneType' object has no attribute 'email'",
  "code_snippet": "def get_profile(user_id):\n  user = db.query(User).filter(id=user_id).first()\n  return user.email",
  "test_command": "pytest tests/test_user.py"
}
```

**Output:** None check needed, suggests defensive programming

### 3. Fix Failing Test
```json
{
  "goal": "Fix the failing test_login test",
  "reproduce_steps": [
    "Run pytest tests/test_auth.py::test_login",
    "Observe assertion error"
  ],
  "error_message": "AssertionError: None != 'john@example.com'",
  "code_snippet": "def test_login():\n  user = login('john', 'pass123')\n  assert user.email == 'john@example.com'",
  "expected_behavior": "Test should pass when valid credentials provided"
}
```

**Output:** Identifies assertion failure, suggests fixture/data issue

### 4. Analyze Complex Stack Trace
```json
{
  "goal": "Debug the IndexError",
  "stack_trace": "[Long multi-level stack trace]",
  "error_message": "IndexError: list index out of range",
  "code_snippet": "items = response['data']\nfirst = items[0]",
  "test_command": "python -m pytest tests/test_api.py -v"
}
```

**Output:** Identifies empty list, suggests bounds checking

## 📈 Output Format

The agent returns comprehensive debugging information:

```json
{
  "status": "success",
  "summary": "Diagnosed TypeError and generated fix suggestions",
  "plan": "1. Identified error type: TypeError\n2. Located issue at: app.py:42\n3. Analyzed root causes\n4. Generated fix suggestions\n5. Verification test prepared",
  "diagnosis": "[Detailed diagnosis markdown]",
  "error_type": "TypeError",
  "location": "app.py:42",
  "suggestions": [
    "Add type checking before operations",
    "Use isinstance() to verify types",
    "Check for None before accessing attributes"
  ],
  "verification": {
    "command": "pytest tests/test_auth.py",
    "passed": false,
    "exit_code": 1,
    "stdout": "[test output]",
    "stderr": "[error output]"
  },
  "artifacts": ["code-fix-abc12345.patch"]
}
```

### Fields

- **status**: "success" or "failed"
- **summary**: Concise description of findings
- **plan**: Step-by-step analysis plan
- **diagnosis**: Detailed markdown diagnosis
- **error_type**: Identified error category
- **location**: File and line number
- **suggestions**: List of fix recommendations
- **verification**: Test execution results
- **artifacts**: Patch file with analysis

## 📝 Sample Diagnosis Output

```markdown
## DIAGNOSIS

**Error Type:** TypeError
**Error Message:** 'NoneType' object is not subscriptable
**Location:** app.py:42
**Function:** process_user_data

## ROOT CAUSE ANALYSIS

Based on the error type and available context, likely causes:

1. Check variable types - Variable is None instead of expected type
2. Verify argument types - Function received wrong argument type
3. Check for None values - Missing None check before operation

## SUGGESTED FIXES

- Add type checking before operations
- Use isinstance() to verify types  
- Check for None before accessing attributes
- Use try/except for type conversions

## CODE SNIPPET

```python
user = db.query(User).filter(id=user_id).first()
username = user['name']  # Error: user is None
```

## EXPECTED BEHAVIOR

Should gracefully handle None user and return appropriate error message.

## REPRODUCTION STEPS

- Query non-existent user
- Try to access attributes
- TypeError occurs

## NEXT ACTIONS

1. Review the suggested fixes above
2. Add None check: `if user is not None:`
3. Run the test: pytest tests/test_user.py
4. Verify the fix resolves the issue
```

## 🔧 Advanced Examples

### Example 1: Production Error Analysis
```bash
# Analyze production error
python mcp_server.py run_agent_tool code-errors-agent \
  "Fix production error in checkout" \
  --targets='["src/checkout/"]' \
  --extra='{
    "error_message": "ZeroDivisionError: float division by zero",
    "stack_trace": "[Production stack trace]",
    "code_snippet": "discount_rate = total_discount / subtotal"
  }'
```

Result: Identifies missing zero check, suggests fix.

### Example 2: Test Debugging
```bash
# Debug failing CI/CD test
python mcp_server.py run_agent_tool code-errors-agent \
  "Fix the flaky test" \
  --targets='["tests/"]' \
  --extra='{
    "test_command": "pytest tests/test_integration.py::test_async_task -v",
    "error_message": "AssertionError: expected 5, got 3",
    "reproduce_steps": ["Run test 3 times", "Fails intermittently"]
  }'
```

Result: Identifies race condition, suggests fixture or mock fix.

### Example 3: Type Error in Data Processing
```bash
python mcp_server.py run_agent_tool code-errors-agent \
  "Fix type error in data pipeline" \
  --targets='["src/pipeline/"]' \
  --extra='{
    "error_message": "TypeError: unsupported operand type(s) for +: '\''int'\'' and '\''str'\''",
    "code_snippet": "price = 100 + customer_discount\n# customer_discount comes from CSV, might be string",
    "test_command": "pytest tests/test_pipeline.py -v"
  }'
```

Result: Identifies type conversion issue, suggests int() conversion.

## 🎓 Tips & Tricks

1. **Always provide error message**: It's the most important signal
2. **Include stack trace**: Helps pinpoint exact location
3. **Add code snippet**: Gives context to the analysis
4. **Use test_command**: Enables verification of fixes
5. **Be specific**: More detail = better diagnosis

## 💡 Common Patterns

### Pattern 1: Missing None Check
**Error:** `AttributeError: 'NoneType' object has no attribute 'x'`

**Fix Pattern:**
```python
# Before
user = get_user(id)
return user.email  # Crashes if user is None

# After
user = get_user(id)
if user is not None:
    return user.email
else:
    return None  # or raise exception
```

### Pattern 2: Type Mismatch
**Error:** `TypeError: unsupported operand type(s) for +: 'int' and 'str'`

**Fix Pattern:**
```python
# Before
total = price + shipping  # shipping might be string

# After
total = price + int(shipping)  # Convert to int first
```

### Pattern 3: Index Out of Bounds
**Error:** `IndexError: list index out of range`

**Fix Pattern:**
```python
# Before
first = items[0]  # Crashes if items is empty

# After
if items:
    first = items[0]
else:
    first = None
```

### Pattern 4: Missing Key
**Error:** `KeyError: 'user_id'`

**Fix Pattern:**
```python
# Before
user_id = data['user_id']  # Crashes if key missing

# After
user_id = data.get('user_id', None)  # Use .get() with default
```

## 🔗 Integration with Other Agents

Works with:
- **File-Sorter Agent**: Organize code by type, then debug errors
- **Agent-Builder**: Use as input for implementation tasks
- **Manager Agent**: Route debugging tasks intelligently

## 📞 Using Artifacts

The patch file contains the full diagnostic report:

```bash
# Read the diagnostic report
cat code-fix-abc12345.patch
```

Use in documentation or team wiki:
```bash
# Extract and save
python mcp_server.py ... | jq -r '.diagnosis' > error_analysis.md
```

## ✨ Workflow Example

```
1. Error occurs in production
   ↓
2. You capture:
   - Error message
   - Stack trace
   - Code snippet
   - Test command to verify fix
   ↓
3. Run Code-Errors Agent with this info
   ↓
4. Get detailed diagnosis and suggestions
   ↓
5. Implement the suggested fix
   ↓
6. Run verification test
   ↓
7. Fix verified and deployed
```

---

**Ready to debug?** Gather your error information and run the agent!
