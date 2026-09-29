# Agent Manager - Configuration & Extension Guide

## Overview

The `taskfile.json` is the central configuration that controls how the agent manager works. This guide shows you how to:
- Understand the structure
- Add new task categories
- Add new agents
- Customize routing rules
- Extend capabilities

## 📐 Taskfile Structure

```
taskfile.json
├── manager                    # Manager metadata
├── agents                      # Available agents and their capabilities
├── task_classification         # Task types and routing info
├── routing_rules              # Keyword patterns for auto-classification
├── workflow                   # Step-by-step workflow definition
├── task_examples              # Real-world example tasks
├── task_priority_levels       # Priority definitions
├── manager_decision_logic     # Logic for manager decisions
└── conversation_flow          # Manager communication templates
```

---

## 🔧 Customization Examples

### Example 1: Adding a New Task Category

If you want to add a "Performance Optimization" category:

1. **Add to `task_classification`**:
```json
{
  "performance_optimization": {
    "name": "Performance Optimization",
    "description": "Optimizing application performance, reducing load times, improving efficiency",
    "assigned_to": "agent-builder",
    "keywords": [
      "performance",
      "optimize",
      "speed",
      "slow",
      "latency",
      "efficiency",
      "throughput"
    ],
    "task_template": {
      "goal": "Optimize application performance",
      "targets": ["src/"],
      "requirements": [
        "Profile current performance",
        "Identify bottlenecks",
        "Implement optimizations",
        "Benchmark improvements",
        "Document performance gains"
      ],
      "depth": "full"
    }
  }
}
```

2. **Add to `routing_rules.priority_keywords`**:
```json
{
  "pattern": "performance|optimize|speed|slow|latency|efficient",
  "category": "performance_optimization"
}
```

3. **Add example task** (optional):
```json
{
  "performance_optimization_request": {
    "user_prompt": "The dashboard takes 10 seconds to load. Optimize for faster performance.",
    "classification": "performance_optimization",
    "assigned_agent": "agent-builder",
    "structured_task": {
      "goal": "Optimize dashboard loading performance",
      "targets": ["src/dashboard/", "src/api/"],
      "requirements": [
        "Profile with performance tools",
        "Identify slow queries/rendering",
        "Implement caching where appropriate",
        "Optimize database queries",
        "Lazy load non-critical components",
        "Benchmark: target <3 second load time",
        "Document optimizations"
      ],
      "depth": "full",
      "checks": ["performance-profile", "test"]
    }
  }
}
```

### Example 2: Adding a New Agent

If you want to add a "Documentation Agent":

1. **Create the agent** (put in prompts directory):
   ```
   ~/Library/Application Support/Code/User/prompts/
   └── documentation-agent/
       ├── run_agent.py  # Must have run(task: dict) -> dict
       └── SKILL.md
   ```

2. **Add to `agents` in taskfile.json**:
```json
{
  "documentation-agent": {
    "name": "Documentation Specialist",
    "role": "Technical Writer",
    "description": "Creates comprehensive documentation, API docs, guides, and examples",
    "capabilities": [
      "write-api-docs",
      "create-guides",
      "write-examples",
      "technical-writing",
      "diagrams"
    ],
    "runner": "run_agent.py"
  }
}
```

3. **Add/update task category** for documentation:
```json
{
  "documentation": {
    "name": "Documentation",
    "description": "Writing and improving documentation",
    "assigned_to": "documentation-agent",  // Changed from agent-builder
    "keywords": ["document", "write docs", "readme", "api docs"],
    "task_template": { ... }
  }
}
```

### Example 3: Adding Routing Rule for Existing Category

To route "performance" tasks to a new agent:

1. **Add routing pattern**:
```json
{
  "pattern": "performance|optimize|speed|profiling",
  "category": "performance_optimization"
}
```

2. **Update category assignment** if needed:
```json
{
  "performance_optimization": {
    "name": "Performance Optimization",
    "assigned_to": "performance-agent",  // If you have a specialized agent
    ...
  }
}
```

---

## 🎯 Task Template Structure

Each task category has a `task_template` that defines what information is sent to the agent:

```json
{
  "goal": "Human-readable description of what needs to be done",
  "targets": ["src/module1", "src/module2"],  // Files to focus on
  "requirements": [
    "Requirement 1",
    "Requirement 2",
    "Run tests",
    "Document changes"
  ],
  "depth": "full",  // or "quick" for faster execution
  "checks": ["lint", "test"]  // Optional: what checks to run
}
```

### Template Best Practices

- **Goal**: Clear, actionable statement
- **Targets**: Specific file paths the agent should focus on
- **Requirements**: List of non-negotiable requirements
- **Depth**: "full" for thorough work, "quick" for speed
- **Checks**: Tests/linters to run for validation

---

## 🚏 Routing Rules Format

Routing rules use regex patterns to classify tasks:

```json
{
  "pattern": "keyword1|keyword2|keyword3",
  "category": "category_name"
}
```

### Pattern Best Practices

- Use `|` (pipe) for OR logic
- Keep patterns lowercase (matching is case-insensitive)
- Be specific enough to avoid false positives
- Order matters: more specific patterns should come first

### Example Patterns

```json
// Too broad - will match too many things
{ "pattern": "do", "category": "..." }

// Better - specific to intent
{ "pattern": "implement|create|build|add (feature|function)", "category": "feature_development" }

// Good - handles variations
{ "pattern": "refactor|optimize|improve|cleanup|reduce duplication", "category": "code_quality" }
```

---

## 📝 Adding Priority Levels

To add or modify priority levels:

```json
{
  "task_priority_levels": {
    "critical": {
      "level": 1,
      "description": "Production down, security breach, data loss",
      "sla": "Immediate",
      "keywords": ["critical", "urgent", "production down"]
    },
    "custom_level": {
      "level": 5,
      "description": "Your custom level description",
      "sla": "Your SLA here",
      "keywords": ["keyword1", "keyword2"]
    }
  }
}
```

---

## 🔄 Workflow Customization

The workflow defines the steps in task execution:

```json
{
  "workflow": {
    "steps": [
      {
        "step": 1,
        "name": "User Input",
        "actor": "User",
        "description": "User provides task"
      },
      {
        "step": 2,
        "name": "Custom Step",
        "actor": "Manager",
        "description": "What the manager does"
      }
    ]
  }
}
```

---

## 💬 Customizing Manager Messages

The `conversation_flow` section controls what the manager says:

```json
{
  "conversation_flow": {
    "manager_to_user": [
      "Custom greeting message",
      "Task Category: {category}",
      "Assigning to: {agent_name}",
      "Custom message about what happens next"
    ],
    "status_updates": [
      "Custom working message...",
      "Custom completion message..."
    ]
  }
}
```

Use `{variable}` placeholders for dynamic content:
- `{category}` - Task category name
- `{agent_name}` - Agent name
- `{goal}` - Task goal
- `{plan}` - Task plan

---

## 🧪 Testing Your Configuration

### Validate JSON Format
```bash
python -m json.tool taskfile.json
```

### Test a New Category
```bash
# List to verify new category shows up
python manager_intelligent.py show-categories

# Test routing with a keyword
python manager_intelligent.py task "your test prompt with new category keywords"
```

### Verify Agent Assignment
Check that:
1. Agent folder exists in prompts
2. `run_agent.py` has `run(task: dict)` function
3. Agent is registered in taskfile.json

---

## 📊 Decision Logic Customization

The `manager_decision_logic` explains how the manager makes decisions:

```json
{
  "manager_decision_logic": {
    "input_analysis": "How manager understands user input",
    "category_matching": "How manager classifies tasks",
    "agent_selection": "How manager picks an agent",
    "task_structuring": "How manager structures the task",
    "execution": "How manager runs the agent",
    "output_handling": "How manager reports results"
  }
}
```

Update these descriptions to match your actual implementation.

---

## 🔗 Adding Cross-Category Dependencies

For complex workflows, you might want one task to delegate to multiple agents:

```json
{
  "complex_feature": {
    "name": "Complex Feature",
    "description": "Features requiring multiple specialists",
    "assigned_to": "agent-builder",  // Primary agent
    "sub_tasks": [
      {
        "type": "implementation",
        "assigned_to": "agent-builder"
      },
      {
        "type": "documentation",
        "assigned_to": "documentation-agent"
      }
    ]
  }
}
```

**Note**: The current `manager_intelligent.py` handles single agents per task. To support this, you'd need to extend it.

---

## 📋 Full Customization Checklist

When adding new functionality:

- [ ] Add task category to `task_classification`
- [ ] Add routing rule to `routing_rules.priority_keywords`
- [ ] Add example task to `task_examples`
- [ ] Create/update agent in prompts directory
- [ ] Add agent to `agents` section
- [ ] Test with `show-categories` command
- [ ] Test with `manager_intelligent.py task "..."`
- [ ] Update documentation
- [ ] Test edge cases

---

## 🎓 Example: Complete Workflow Extension

Let's say you want to add a "DevOps/Infrastructure" category:

1. **Create agent** (or use existing):
   ```
   ~/Library/Application Support/Code/User/prompts/devops-agent/
   └── run_agent.py
   ```

2. **Update taskfile.json**:

   Add to `agents`:
   ```json
   {
     "devops-agent": {
       "name": "DevOps Specialist",
       "role": "Infrastructure Engineer",
       "description": "Handles deployment, infrastructure, CI/CD configuration",
       "capabilities": ["deployment", "docker", "ci-cd", "infrastructure"],
       "runner": "run_agent.py"
     }
   }
   ```

   Add to `task_classification`:
   ```json
   {
     "devops": {
       "name": "DevOps & Infrastructure",
       "description": "Deployment, infrastructure, CI/CD pipeline work",
       "assigned_to": "devops-agent",
       "keywords": ["deploy", "docker", "kubernetes", "ci", "cd", "pipeline", "infrastructure"],
       "task_template": {
         "goal": "Set up or improve infrastructure",
         "targets": ["deploy/", "config/"],
         "requirements": ["Document setup", "Add security checks"],
         "depth": "full"
       }
     }
   }
   ```

   Add to `routing_rules`:
   ```json
   {
     "pattern": "deploy|docker|kubernetes|ci/cd|pipeline|infrastructure|helm",
     "category": "devops"
   }
   ```

   Add example:
   ```json
   {
     "devops_request": {
       "user_prompt": "Set up Docker containers and GitHub Actions CI/CD pipeline",
       "classification": "devops",
       "assigned_agent": "devops-agent",
       "structured_task": { ... }
     }
   }
   ```

3. **Test**:
   ```bash
   python manager_intelligent.py show-categories  # See new category
   python manager_intelligent.py task "Dockerize the application"  # Should route to devops-agent
   ```

---

## 🚀 Advanced: Custom Classification Logic

The `manager_intelligent.py` uses simple regex matching. For more sophisticated classification:

1. Modify `classify_task()` in `manager_intelligent.py`
2. Add ML-based classification (if desired)
3. Add multi-step decision trees
4. Add confidence scoring

Example modification:
```python
def classify_task(user_prompt: str, taskfile: Dict) -> Tuple[str, Dict]:
    # Custom logic here
    confidence_scores = {}
    for category, rules in taskfile['task_classification'].items():
        score = calculate_score(user_prompt, category)  # Your logic
        confidence_scores[category] = score
    
    best_category = max(confidence_scores, key=confidence_scores.get)
    return best_category, taskfile['task_classification'][best_category]
```

---

## 📚 Resources

- `taskfile.json` - See actual structure
- `manager_intelligent.py` - Implementation details
- `INTELLIGENT_MANAGER_README.md` - Full documentation
- `QUICK_REFERENCE.md` - Quick examples

---

**Now you can customize the agent manager for your specific needs!** 🎉
