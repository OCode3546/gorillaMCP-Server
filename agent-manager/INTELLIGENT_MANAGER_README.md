# Agent Manager with Intelligent Task Routing

A sophisticated task orchestration system that implements a real-world manager-to-employees workflow. The manager intelligently analyzes user requests, classifies them, and routes them to specialized agents for execution.

## 📋 Overview

```
┌─────────────────┐
│   USER INPUT    │ "Implement a login form with tests"
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────┐
│   MANAGER (Task Analysis)            │
│ • Classify task type                 │
│ • Analyze keywords & context         │
│ • Determine requirements             │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│   AGENT ROUTING                      │
│ • Select appropriate agent           │
│ • Structure formal task JSON         │
│ • Request approval                   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│   SPECIALIST AGENT (Execution)       │
│ • Execute work                       │
│ • Generate artifacts (patches)       │
│ • Return results & status            │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│   RESULTS REVIEW                     │
│ • Display artifacts                  │
│ • Show status & summary              │
│ • Ready for approval/merge           │
└──────────────────────────────────────┘
```

## 🗂️ Files

- **`taskfile.json`** - Central configuration defining:
  - Task categories and classifications
  - Agent capabilities and routing rules
  - Task templates for different work types
  - Workflow orchestration logic
  - Example task prompts

- **`manager_intelligent.py`** - Enhanced manager that:
  - Loads taskfile configuration
  - Classifies user tasks via keyword analysis
  - Routes to appropriate agents
  - Structures unstructured input into formal tasks
  - Orchestrates execution and reporting

- **`manager.py`** - Simple original manager (still available)
  - Basic agent discovery and execution
  - Direct task specification

## 📚 Task Categories

The taskfile defines these task categories:

### 1. **Feature Development** 
Implementing new features and functionality
- **Keywords**: implement, create, build, add feature, new capability
- **Assigned to**: agent-builder
- **Example**: "Implement a user authentication module with login and signup"

### 2. **Code Quality & Refactoring**
Improving code quality, reducing duplication, optimization
- **Keywords**: refactor, optimize, improve, cleanup, reduce duplication
- **Assigned to**: agent-builder
- **Example**: "Refactor the database module to eliminate connection handling duplication"

### 3. **Bug Fixes**
Fixing bugs and issues in existing code
- **Keywords**: fix bug, broken, crash, error, not working
- **Assigned to**: agent-builder
- **Example**: "Fix the password reset email that's not being sent"

### 4. **Testing & QA**
Adding tests, improving coverage, edge case testing
- **Keywords**: add tests, test coverage, unit test, integration test, qa
- **Assigned to**: agent-builder
- **Example**: "Add comprehensive tests for the payment processing module"

### 5. **Code Review & Audit**
Security reviews, best practices, pre-PR audits
- **Keywords**: audit, review, check, inspect, security, pre-pr
- **Assigned to**: agent-builder
- **Example**: "Audit the API handlers for security vulnerabilities before merging"

### 6. **Documentation**
Writing and improving documentation
- **Keywords**: document, write docs, readme, comments, docstring
- **Assigned to**: agent-builder
- **Example**: "Write comprehensive API documentation"

## 🚀 Quick Start

### List Available Agents
```bash
cd ~/Library/Application\ Support/Code/User/prompts/agent-manager/
python manager_intelligent.py list-agents
```

Output shows:
- Agent names and IDs
- Roles and descriptions
- Capabilities
- Runner paths

### Show Task Categories
```bash
python manager_intelligent.py show-categories
```

Output shows:
- All supported task types
- Keywords that trigger each category
- Assignment rules

### Execute a Task (Simple)
```bash
python manager_intelligent.py task "Implement a new user preferences page"
```

The manager will:
1. ✓ Analyze your prompt
2. ✓ Classify as "feature_development"
3. ✓ Route to agent-builder
4. ✓ Show the plan
5. ✓ Ask for approval
6. ✓ Execute and report results

### Execute a Task (Manual Agent Override)
```bash
python manager_intelligent.py task "Audit security" --agent agent-builder
```

### Execute a Task (Skip Approval)
```bash
python manager_intelligent.py task "Add unit tests" --skip-approval
```

## 📋 How It Works: The Workflow

### Phase 1: User Input
User provides a natural language task description:
```
"I need to add a new payment gateway integration with tests"
```

### Phase 2: Manager Analysis
Manager reads the taskfile and:
1. **Analyzes keywords** in the prompt
2. **Matches against routing rules** to determine category
3. **Selects appropriate agent** from the configuration
4. **Structures the task** into formal JSON format

### Phase 3: Routing
Manager presents the plan to the user:
```
Task classified as: Feature Development
Assigned to: Builder Agent (Engineer/Specialist)
Plan:
  - goal: Add payment gateway integration with tests
  - targets: [src/payment/, tests/]
  - requirements:
    - Support multiple payment methods
    - Include unit tests
    - Add integration tests
    - Document API
```

### Phase 4: Approval & Execution
User confirms (or manager skips with --skip-approval):
```
[MANAGER] Proceed with task execution? [y/n]: y
[MANAGER] Delegating to Builder Agent...
```

### Phase 5: Agent Execution
Agent executes the task:
- Inspects target files
- Runs linters/tests if requested
- Creates patches with changes
- Generates artifacts

### Phase 6: Results
Manager collects and reports:
```
Status: success
Summary: Implemented payment gateway integration
Artifacts Generated:
  - /path/to/patch-abc123.patch
  - /path/to/patch-def456.patch
```

## 🔧 Using the Taskfile

### Understanding taskfile.json Structure

```json
{
  "manager": { ... },           // Manager metadata
  "agents": { ... },            // Available agents and capabilities
  "task_classification": { ... },  // Task types and routing
  "routing_rules": { ... },     // Keyword patterns for classification
  "workflow": { ... },          // Step-by-step workflow definition
  "task_examples": { ... },     // Real example tasks
  "task_priority_levels": { ... }, // Priority definitions
  "manager_decision_logic": { ... }  // How manager makes decisions
}
```

### Adding New Task Categories

1. Edit `taskfile.json`
2. Add entry to `task_classification`:
```json
{
  "custom_category": {
    "name": "Custom Work Type",
    "description": "What this category handles",
    "assigned_to": "agent-builder",
    "keywords": ["keyword1", "keyword2"],
    "task_template": {
      "goal": "Template goal",
      "targets": ["src/"],
      "requirements": ["req1", "req2"]
    }
  }
}
```

3. Add routing rule to match keywords:
```json
{
  "pattern": "keyword1|keyword2|keyword3",
  "category": "custom_category"
}
```

### Adding New Agents

1. Create agent with `run_agent.py` or `run_agent.js`
2. Add to `agents` in taskfile.json:
```json
{
  "agents": {
    "new-agent": {
      "name": "New Agent Name",
      "role": "Specialist",
      "description": "What it does",
      "capabilities": ["cap1", "cap2"],
      "runner": "run_agent.py"
    }
  }
}
```

## 💬 Example Conversations

### Example 1: Feature Implementation
```
USER: "Add a dark mode toggle to the settings page"

MANAGER: ✓ Task classified as: Feature Development
         ✓ Assigned to: Builder Agent
         
PLAN:
  Goal: Add dark mode toggle to settings page
  Targets: [src/ui/settings/, src/styles/]
  Requirements:
    - Add toggle control
    - Implement theme switching logic
    - Persist user preference
    - Test on multiple browsers
    - Update documentation

MANAGER: Proceed? [y/n]: y

BUILDER: [Working on dark mode feature...]
         [Creating patches...]
         [Running tests...]

MANAGER: ✓ Status: success
         ✓ Artifacts: patch-abc123.patch
```

### Example 2: Bug Fix
```
USER: "Fix the bug where long user names break the dashboard layout"

MANAGER: ✓ Task classified as: Bug Fix
         ✓ Assigned to: Builder Agent
         
PLAN:
  Goal: Fix layout break with long user names
  Targets: [src/dashboard/]
  Requirements:
    - Reproduce the issue
    - Identify root cause
    - Implement CSS/layout fix
    - Add regression test
    - Verify on different screen sizes

MANAGER: Proceed? [y/n]: y

BUILDER: [Reproducing issue...]
         [Analyzing layout code...]
         [Creating fix...]
         [Running tests...]

MANAGER: ✓ Status: success
         ✓ Summary: Fixed layout break with text truncation
         ✓ Artifacts: patch-def456.patch
```

### Example 3: Code Review
```
USER: "Review the new API endpoints for security issues"

MANAGER: ✓ Task classified as: Code Review & Audit
         ✓ Assigned to: Builder Agent
         
PLAN:
  Goal: Security audit of API endpoints
  Targets: [src/api/]
  Requirements:
    - Check for injection vulnerabilities
    - Verify input validation
    - Ensure proper auth/permissions
    - Run security linters
    - Report findings

MANAGER: Proceed? [y/n]: y

BUILDER: [Analyzing endpoint code...]
         [Running security checks...]
         [Reviewing auth logic...]

MANAGER: ✓ Status: success
         ✓ Summary: Security audit complete, 2 minor issues found
         ✓ Artifacts: patch-ghi789.patch (with recommendations)
```

## 🔌 Integration

### Using with Original Manager
The enhanced manager is fully compatible with the simple manager:

```bash
# Still works with simple manager
python manager.py run --agent agent-builder --task-json '{"goal":"..."}'

# Or use enhanced manager with same task
python manager_intelligent.py task "Your natural language task"
```

### Programmatic Usage

```python
from manager_intelligent import classify_task, structure_task, load_taskfile

taskfile = load_taskfile()
category, category_def = classify_task("Implement a login form", taskfile)
task = structure_task("Implement a login form", category, taskfile)

# Now pass task to agent
print(json.dumps(task, indent=2))
```

## 🎯 Best Practices

1. **Be Descriptive**: The more detail in your prompt, the better the routing
   - ✓ "Add email verification for user signup with comprehensive tests"
   - ✗ "Add email stuff"

2. **Include Context**: Mention affected files or modules
   - ✓ "Refactor src/utils/validators.py to reduce duplication"
   - ✗ "Make the code better"

3. **Specify Requirements**: Let the manager know what matters
   - ✓ "Add unit tests, run linters, ensure backward compatibility"
   - ✗ "Fix it"

4. **Use Keywords**: Keywords help with classification
   - For features: "implement", "add", "create", "build"
   - For bugs: "fix", "broken", "crash", "error"
   - For refactoring: "refactor", "optimize", "improve"

## 🔍 Troubleshooting

### Agent Not Found
```
ERROR: Agent 'agent-builder' not found
```
Solution: Run `python manager_intelligent.py list-agents` to see available agents

### Task Classification Incorrect
The manager uses keyword matching. If classified wrong, you can:
```bash
python manager_intelligent.py task "your prompt" --agent specific-agent
```

### Taskfile Issues
```
ERROR: taskfile.json not found or invalid
```
Solution: Ensure taskfile.json is in the same directory as manager_intelligent.py

## 📖 Reference

- `taskfile.json` - Full configuration with all task types and routing rules
- `manager.py` - Original simple manager (for reference)
- `manager_intelligent.py` - New intelligent manager with routing
- Agent runners - Each agent's `run_agent.py` or `run_agent.js`

## 🤝 Workflow Summary

```
INPUT → ANALYZE → CLASSIFY → ROUTE → STRUCTURE → APPROVE → EXECUTE → REPORT
```

**Manager to User**: "I understand what you need. Let me find the right person."
**Manager to Agent**: "Here's the detailed task. Let's get it done."
**Manager to User**: "Here are the results and artifacts ready for review."

---

Ready to delegate? Run:
```bash
python manager_intelligent.py task "Your task description here"
```
