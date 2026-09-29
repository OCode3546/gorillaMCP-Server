# Agent Manager - Quick Reference Guide

## 🎯 Common Tasks

### Before You Start
```bash
# Navigate to manager directory
cd ~/Library/Application\ Support/Code/User/prompts/agent-manager/
```

### 1. See What's Available
```bash
# List all agents
python manager_intelligent.py list-agents

# Show all task categories  
python manager_intelligent.py show-categories
```

---

## 📝 Task Examples

### Feature Development
```bash
python manager_intelligent.py task "Implement a user profile page with settings"
python manager_intelligent.py task "Add social login integration using OAuth"
python manager_intelligent.py task "Create a new API endpoint for data export"
```

### Bug Fixes
```bash
python manager_intelligent.py task "Fix the login button not working on mobile"
python manager_intelligent.py task "Fix memory leak in the background worker"
python manager_intelligent.py task "Fix 404 error when accessing old URLs"
```

### Code Quality
```bash
python manager_intelligent.py task "Refactor the database connection pool to remove duplication"
python manager_intelligent.py task "Optimize the image processing pipeline for performance"
python manager_intelligent.py task "Clean up unused imports across the codebase"
```

### Testing
```bash
python manager_intelligent.py task "Add unit tests for the payment module with edge cases"
python manager_intelligent.py task "Improve test coverage for authentication to >90%"
python manager_intelligent.py task "Add integration tests for the email service"
```

### Code Review & Security
```bash
python manager_intelligent.py task "Audit the API endpoints for security vulnerabilities"
python manager_intelligent.py task "Review the new database migration for best practices"
python manager_intelligent.py task "Perform a pre-PR code review of the auth module"
```

### Documentation
```bash
python manager_intelligent.py task "Document the new API endpoints with examples"
python manager_intelligent.py task "Write setup and installation guide"
python manager_intelligent.py task "Add JSDoc comments to all public functions"
```

---

## ⚙️ Advanced Options

### Override Agent Assignment
```bash
# Force specific agent if auto-routing is wrong
python manager_intelligent.py task "your task here" --agent agent-builder
```

### Skip Approval (Run Immediately)
```bash
# Useful for automation/CI/CD pipelines
python manager_intelligent.py task "your task here" --skip-approval
```

### Combined
```bash
# Override agent AND skip approval
python manager_intelligent.py task "your task here" --agent agent-builder --skip-approval
```

---

## 📊 Workflow Flow

```
1. You provide task
   ↓
2. Manager analyzes it
   ↓
3. Manager shows plan
   ↓
4. You approve (or --skip-approval)
   ↓
5. Agent executes
   ↓
6. Results with artifacts
   ↓
7. Review and merge
```

---

## 🎓 Keyword Reference

**Use these keywords to help routing:**

| Category | Keywords |
|----------|----------|
| Feature | implement, create, build, add, new |
| Refactor | refactor, optimize, improve, cleanup |
| Bug Fix | fix, broken, crash, error, bug |
| Testing | test, tests, coverage, unit test, integration |
| Review | audit, review, check, inspect, security |
| Docs | document, readme, docstring, api docs |

---

## 💡 Pro Tips

1. **Be Specific**: More details = better routing
   ```bash
   # Good
   python manager_intelligent.py task "Add unit tests for auth.py covering login, logout, and password reset scenarios"
   
   # Less Good
   python manager_intelligent.py task "Add tests"
   ```

2. **Mention Files**: Helps with targeting
   ```bash
   python manager_intelligent.py task "Refactor src/db/connection.py to eliminate the connection pooling duplication"
   ```

3. **Include Requirements**: Guides the work
   ```bash
   python manager_intelligent.py task "Implement dark mode toggle with localStorage persistence, tests, and accessibility support"
   ```

4. **Use Automation**: Skip approval in scripts
   ```bash
   python manager_intelligent.py task "Run linters and fix style issues" --skip-approval
   ```

---

## 📋 Expected Response Flow

### Step 1: Task Received
```
[MANAGER] Received task request. Analyzing...
```

### Step 2: Classification
```
✓ Task classified as: Feature Development
```

### Step 3: Assignment
```
✓ Assigned to: Builder Agent
  Role: Engineer / Specialist
```

### Step 4: Plan Review
```
[MANAGER] TASK PLAN
{
  "goal": "Implement a user profile page",
  "targets": ["src/"],
  "requirements": [...],
  "depth": "full"
}
```

### Step 5: Approval
```
[MANAGER] Proceed with task execution? [y/n]:
```

### Step 6: Execution
```
[MANAGER] Delegating to Builder Agent...
```

### Step 7: Results
```
Status: success
Summary: Completed profile page implementation
Artifacts Generated:
  - /path/to/patch-abc123.patch
```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `taskfile.json` | Master configuration with all task types |
| `manager_intelligent.py` | Smart router and orchestrator |
| `manager.py` | Simple original manager (still works) |

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not found | Run `list-agents` to see available agents |
| Wrong category assigned | Use `--agent` flag to override |
| Command not found | Check you're in the right directory |
| taskfile.json missing | Ensure it's in agent-manager folder |

---

## 🎮 Real-World Scenario

### Scenario: Your app has a bug
```bash
# 1. Report the bug using natural language
$ python manager_intelligent.py task "Fix the logout button that doesn't redirect to login page"

# Manager analyzes and routes to agent
✓ Task classified as: Bug Fix
✓ Assigned to: Builder Agent

# 2. See the plan
[MANAGER] TASK PLAN
{
  "goal": "Fix the logout button redirect issue",
  "targets": ["src/auth/", "src/ui/"],
  "requirements": [
    "Reproduce the issue",
    "Add regression test",
    "Verify fix works",
    "No side effects"
  ]
}

# 3. Approve
[MANAGER] Proceed? [y/n]: y

# 4. Agent does the work
[MANAGER] Delegating to Builder Agent...

# 5. Review results
Status: success
Summary: Fixed logout redirect logic
Artifacts:
  - patch-def456.patch
```

---

## 📞 Need More Help?

- Full docs: See `INTELLIGENT_MANAGER_README.md`
- Task types: Run `show-categories`
- Available agents: Run `list-agents`
- Examples: Check taskfile.json `task_examples` section

---

**Ready to delegate? Just run:**
```bash
python manager_intelligent.py task "what needs to be done"
```

The manager handles the rest! 🚀
