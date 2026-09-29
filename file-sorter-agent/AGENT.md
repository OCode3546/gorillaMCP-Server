# Agent: File Sorter — MCP Compatible

**Purpose:** Intelligently categorizes, organizes, and sorts files in a workspace based on type, size, date, or custom criteria. Generates organization reports and optional file move operations.

**Capabilities:**
- Sort files by type (code, docs, media, config, etc.)
- Organize by date modified (today, this week, this month, etc.)
- Group by file size (small, medium, large)
- Generate organization reports
- Create suggested folder structure
- Identify duplicate files
- Find orphaned or unused files
- Custom sorting rules

**Entrypoint:** `run_agent.py` with `run(task: dict) -> dict` function

**Task Schema:**
```json
{
  "goal": "Sort files in src/ by type and organize into folders",
  "targets": ["src/", "public/"],
  "sort_by": "type|date|size",
  "generate_report": true,
  "create_structure": true,
  "rules": {
    "group_by_extension": true,
    "create_subfolders": true,
    "pattern_rules": [...]
  }
}
```

**Returns:**
- Status (success/failed)
- Summary of organization
- File groups and statistics
- Organization report
- Suggested folder structure
- Optional: patch file with mv commands
