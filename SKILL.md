# Agent Manager Skill

## Purpose
This repository follows a simple orchestration pattern:

User -> Manager -> Employee Agent -> Result -> User

The manager is the first decision-maker after the user request. The employee agent is the last executor for a specific task. The manager decides which employee is needed based on the task category, routing rules, and the assigned agent capabilities.

## Hierarchy and execution order

1. User
   - Sends the original prompt or request.
   - Defines the goal, constraints, and desired outcome.

2. Manager
   - Reads the request.
   - Classifies it using the task routing rules in agent-manager/taskfile.json.
   - Selects the correct employee agent.
   - Structures the task into a formal goal/targets/requirements payload.
   - Requests approval if required.
   - Launches the chosen agent.

3. Employee Agent
   - Receives the structured task.
   - Performs the specialized work.
   - Returns status, summary, plan, and artifacts.

4. Manager
   - Collects the result.
   - Reports back to the user.
   - May continue orchestration or delegate further work if needed.

## Who is first and who is last

- First in the chain: the User, because the request originates there.
- First operational coordinator: the Manager, because it decides the route before any worker runs.
- Last in the chain for a single task: the selected Employee Agent, because it performs the actual work and returns the final result for that specific assignment.

This means the manager is not the last step in a task; it is the dispatcher. The employee agent is the final executor of the actual task.

## Agent roles in this repo

- agent-builder
  - General implementation and refactoring work.
  - Best for feature development, refactoring, tests, documentation, and code review.

- file-sorter-agent
  - File organization, sorting, cleanup, and reporting.
  - Best for workspace organization, file grouping, large-file discovery, and structure suggestions.

- code-errors-agent
  - Debugging and error diagnosis.
  - Best for stack traces, TypeError/AttributeError/ZeroDivisionError, failing tests, and fix suggestions.

## Routing principle

The manager should always follow this order:

1. Understand the user request.
2. Match it against task categories and keywords.
3. Pick the most relevant employee agent.
4. Delegate only that task.
5. Return results to the user.

## Decision rule for LLMs

When handling a request in this repo:

- Do not start by invoking an employee directly unless the task is already explicit and single-purpose.
- Prefer the manager as the first decision point.
- Treat the manager as the orchestrator and the agent as the executor.
- If a task includes file organization, debugging, or code building, route it to the matching specialized agent.

## Repository-specific files

- agent-manager/taskfile.json
  - Defines the task categories, keywords, and agent mapping.

- agent-manager/manager_intelligent.py
  - Implements the routing logic and task execution flow.

## Canonical interpretation

The intended chain is:

User request
  -> Manager decides category
  -> Manager assigns to one employee
  -> Employee completes the work
  -> Manager reports final result

The manager is the first orchestrator, and the selected employee is the final task executor for that task.
