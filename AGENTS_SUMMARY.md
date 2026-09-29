# New Agents Summary — MCP Server Integration

Two fully functional agents have been created and integrated with your MCP server. Both follow the same pattern as the existing `agent-builder` agent.

## 🎯 Agents Created

### 1. File Sorter Agent (`file-sorter-agent`)
**Purpose:** Organize and categorize files in your workspace

**Location:** `/Agents & MCP Server/file-sorter-agent/`

**Key Features:**
- Sort files by type, date, or size
- Generate organization reports
- Suggest folder structures
- Identify file patterns
- Calculate storage usage

**What's Inside:**
- `AGENT.md` - Agent metadata and description
- `run_agent.py` - Main execution logic
- `README.md` - Complete usage guide
- `outgoing_patches/` - Generated reports and suggestions

**Entrypoint:** `run_agent.py` with `run(task: dict) -> dict` function

### 2. Code & Errors Helper Agent (`code-errors-agent`)
**Purpose:** Debug and fix code errors and issues

**Location:** `/Agents & MCP Server/code-errors-agent/`

**Key Features:**
- Analyze compiler and runtime errors
- Parse and extract stack trace information
- Review failing tests
- Generate targeted fix suggestions
- Verify fixes with tests

**What's Inside:**
- `AGENT.md` - Agent metadata and description
- `run_agent.py` - Main execution logic
- `README.md` - Complete usage guide
- `outgoing_patches/` - Diagnostic reports

**Entrypoint:** `run_agent.py` with `run(task: dict) -> dict` function

---

## 🔌 How They Connect to MCP Server

The MCP server automatically discovers agents by looking for folders with:
1. A `run_agent.py` file (or `.js`)
2. An `AGENT.md` file for metadata

**Automatic Discovery:**
```python
# mcp_server.py finds agents via this process:
def discover_agents():
    for folder in workspace:
        if folder/run_agent.py exists:
            agents.append({
                "name": folder.name,
                "path": folder/run_agent.py,
                "description": read(folder/AGENT.md)
            })
```

**No Configuration Needed!** The agents are ready to use immediately.

---

## 🚀 Using the Agents

### List Available Agents

```bash
cd ~/Library/Application\ Support/Code/User/prompts/
python ../../../Documents/Agents\ \&\ MCP\ Server/mcp_server.py --print-manifest | jq '.supported_tools'
```

Or use the MCP tool directly:
```bash
python mcp_server.py run_agent_tool file-sorter-agent "Show me what this does"
```

### File Sorter Agent Examples

#### Example 1: Organize by File Type
```bash
python ~/Library/Application\ Support/Code/User/prompts/file-sorter-agent/run_agent.py \
  --task-json '{
    "goal": "Organize project files by type",
    "targets": ["src/", "tests/", "docs/"],
    "sort_by": "type"
  }'
```

**Output:**
```json
{
  "status": "success",
  "summary": "Analyzed 127 files across 7 categories. Total size: 23.45 MB",
  "files_found": 127,
  "total_size_mb": 23.45,
  "groups": {
    "code": 62,
    "config": 8,
    "document": 15,
    "markup": 12,
    "media": 18,
    "other": 12
  },
  "report": "[Formatted text report]",
  "artifacts": ["file-sort-xyz123.patch"]
}
```

#### Example 2: Find Large Files
```bash
python ~/Library/Application\ Support/Code/User/prompts/file-sorter-agent/run_agent.py \
  --task-json '{
    "goal": "Find files using most disk space",
    "targets": ["./"],
    "sort_by": "size"
  }'
```

#### Example 3: Check Recently Modified Files
```bash
python ~/Library/Application\ Support/Code/User/prompts/file-sorter-agent/run_agent.py \
  --task-json '{
    "goal": "Find recently modified files for backup",
    "targets": ["src/", "config/"],
    "sort_by": "date"
  }'
```

### Code Errors Agent Examples

#### Example 1: Fix TypeError
```bash
python ~/Library/Application\ Support/Code/User/prompts/code-errors-agent/run_agent.py \
  --task-json '{
    "goal": "Fix TypeError in authentication",
    "error_message": "TypeError: '\''NoneType'\'' object is not subscriptable",
    "code_snippet": "user = db.get_user(user_id)\nname = user['\''name'\'']",
    "test_command": "pytest tests/test_auth.py::test_login"
  }'
```

**Output:**
```json
{
  "status": "success",
  "summary": "Diagnosed TypeError and generated fix suggestions",
  "error_type": "TypeError",
  "location": "auth.py:42",
  "diagnosis": "[Detailed markdown diagnosis]",
  "suggestions": [
    "Add type checking before operations",
    "Use isinstance() to verify types",
    "Check for None before accessing attributes"
  ],
  "verification": {
    "command": "pytest tests/test_auth.py::test_login",
    "passed": false,
    "exit_code": 1
  },
  "artifacts": ["code-fix-abc123.patch"]
}
```

#### Example 2: Debug Stack Trace
```bash
python ~/Library/Application\ Support/Code/User/prompts/code-errors-agent/run_agent.py \
  --task-json '{
    "goal": "Debug the IndexError",
    "stack_trace": "File \"app.py\", line 42, in process\nlist_items[0]\nIndexError: list index out of range",
    "error_message": "IndexError: list index out of range",
    "code_snippet": "items = response.get(\"data\", [])\nfirst = items[0]"
  }'
```

#### Example 3: Fix Failing Test
```bash
python ~/Library/Application\ Support/Code/User/prompts/code-errors-agent/run_agent.py \
  --task-json '{
    "goal": "Fix the flaky test",
    "test_command": "pytest tests/test_integration.py::test_checkout -v",
    "error_message": "AssertionError: None != '\''success'\''",
    "expected_behavior": "Test should pass with mock payment service"
  }'
```

---

## 🔗 Integration Examples

### Via MCP Server Tools

```bash
# List all agents
python mcp_server.py list_agents

# Get agent details
python mcp_server.py get_agent file-sorter-agent

# Run an agent
python mcp_server.py run_agent_tool file-sorter-agent \
  "Organize my project files" \
  --targets='["src/", "tests/"]' \
  --extra='{"sort_by":"type"}'

# Orchestrate multiple agents
python mcp_server.py orchestrate_agents_tool \
  '["file-sorter-agent", "code-errors-agent"]' \
  "Analyze and organize project" \
  --targets='["src/"]'
```

### Via Management Script

```bash
# Using the intelligent manager
cd ~/Library/Application\ Support/Code/User/prompts/agent-manager/

# Check agent status
python manager_intelligent.py list-agents

# Route a task that triggers file-sorter
python manager_intelligent.py task "Organize files in the project"

# Route a task that triggers code-errors
python manager_intelligent.py task "Fix the TypeError in auth module"
```

---

## 📊 Agent Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (mcp_server.py)               │
│  Discovers agents automatically from workspace folders      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │agent-builder │ │file-sorter   │ │code-errors   │
        │              │ │              │ │              │
        │• Build code  │ │• Sort files  │ │• Debug bugs  │
        │• Add tests   │ │• Organize    │ │• Fix errors  │
        │• Refactor    │ │• Report      │ │• Verify      │
        └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🧪 Testing the Agents

### Quick Test - File Sorter

```bash
# Create test task file
cat > test_file_sorter.json << 'EOF'
{
  "goal": "Test file sorter on current directory",
  "targets": ["./"],
  "sort_by": "type"
}
EOF

# Run agent
python file-sorter-agent/run_agent.py --task-file test_file_sorter.json
```

### Quick Test - Code Errors

```bash
# Create test task file
cat > test_code_errors.json << 'EOF'
{
  "goal": "Test error analysis",
  "error_message": "TypeError: 'NoneType' object is not subscriptable",
  "code_snippet": "result = None\nvalue = result['key']"
}
EOF

# Run agent
python code-errors-agent/run_agent.py --task-file test_code_errors.json
```

---

## 📁 File Structure

```
Agents & MCP Server/
├── mcp_server.py              # ← Auto-discovers agents below
├── test_mcp_server.py
│
├── agent-builder/             # ← Existing agent
│   ├── AGENT.md
│   ├── run_agent.py
│   └── outgoing_patches/
│
├── file-sorter-agent/         # ← NEW: File organization
│   ├── AGENT.md
│   ├── run_agent.py
│   ├── README.md
│   └── outgoing_patches/
│
├── code-errors-agent/         # ← NEW: Debug & fix errors
│   ├── AGENT.md
│   ├── run_agent.py
│   ├── README.md
│   └── outgoing_patches/
│
└── agent-manager/             # ← Intelligent routing
    ├── taskfile.json
    ├── manager.py
    └── manager_intelligent.py
```

---

## 🔧 Extending the Agents

### Add File Categories (File Sorter)

In `file-sorter-agent/run_agent.py`, modify `FILE_CATEGORIES`:

```python
FILE_CATEGORIES = {
    "code": [...],
    "your_category": [".ext1", ".ext2"],  # Add this
    ...
}
```

### Add Error Types (Code Errors)

In `code-errors-agent/run_agent.py`, modify `error_patterns`:

```python
error_patterns = {
    r"YourError": ("YourError", ["Fix 1", "Fix 2"]),  # Add this
    ...
}
```

### Create New Agent Template

Follow the same pattern:

```python
# new-agent/run_agent.py
def run(task: dict) -> dict:
    """Main execution function."""
    return {
        "status": "success",
        "summary": "Task completed",
        "plan": "Step-by-step plan",
        "artifacts": [],  # Patch files
    }

if __name__ == "__main__":
    # CLI support
    pass
```

---

## 💡 Use Cases

### Scenario 1: Project Onboarding
New developer joins project:
```bash
# Understand project structure
python mcp_server.py run_agent_tool file-sorter-agent \
  "Help me understand this project structure"

# Get a report to review
```

### Scenario 2: Production Bug Fix
Error in production:
```bash
# Analyze the error
python mcp_server.py run_agent_tool code-errors-agent \
  "Fix the production error" \
  --extra='{
    "error_message": "[production error]",
    "stack_trace": "[trace from logs]"
  }'

# Get targeted fix suggestions
```

### Scenario 3: Repository Cleanup
Need to organize files:
```bash
# Find what's taking space
python mcp_server.py run_agent_tool file-sorter-agent \
  "Show me what's using disk space" \
  --extra='{"sort_by":"size"}'

# Get organizational recommendations
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `file-sorter-agent/README.md` | Complete file sorter guide |
| `code-errors-agent/README.md` | Complete error helper guide |
| `file-sorter-agent/AGENT.md` | Metadata and schema |
| `code-errors-agent/AGENT.md` | Metadata and schema |
| `mcp_server.py` | Auto-discovery logic |

---

## ✅ Verification

The agents are ready to use immediately. No additional configuration needed!

To verify agents are discoverable:

```bash
cd ~/Library/Application\ Support/Code/User/prompts/

# Should list 3 agents now
python ../../../Documents/Agents\ \&\ MCP\ Server/mcp_server.py \
  --print-manifest | jq '.workspace_root'

# Run discovery
python ../../../Documents/Agents\ \&\ MCP\ Server/mcp_server.py \
  2>&1 | grep -i "agent"
```

---

## 🎓 Next Steps

1. **Explore agents**: Read their README files
2. **Test agents**: Run example commands above
3. **Use in workflows**: Integrate with MCP server tools
4. **Extend as needed**: Customize categories or error types
5. **Create more**: Use template for additional agents

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Organize files by type | `file-sorter-agent` with `sort_by: type` |
| Find large files | `file-sorter-agent` with `sort_by: size` |
| Check recent changes | `file-sorter-agent` with `sort_by: date` |
| Debug error | `code-errors-agent` with error message |
| Fix failing test | `code-errors-agent` with test output |
| List all agents | `python mcp_server.py --print-manifest` |

---

**Both agents are fully functional and ready to use with your MCP server!** 🚀
