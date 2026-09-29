# Agent: File Sorter — MCP Compatible

**Purpose:** Categorizes files by type, extension, size, date or custom rules and moves (or copies) them into folders. Dry run by default; every applied sort can be undone.

**Capabilities:**
- Plan (dry run) → apply → undo workflow, with a manifest recorded for every applied run
- Sort by type (images, videos, audio, documents, code, installers, …), extension, size, relative date, month or year
- Custom pattern rules (`Screenshot*` → `Screenshots/`) and custom categories
- Include/exclude globs, recursive or top-level only, optional separate destination
- Name conflicts renamed (`file (1).pdf`), skipped, or overwritten
- Copy instead of move
- Duplicate detection by content hash (report, or move extras to `duplicates/`)
- Removes folders left empty by the sort
- Safety: skips `.git`, virtualenvs, `node_modules`, hidden files, app bundles and partial downloads; refuses system paths; won't apply inside a git repo without `force`

**Entrypoint:** `run_agent.py` with `run(task: dict) -> dict` function

**Task Schema:**
```json
{
  "goal": "Sort my Downloads folder",
  "targets": ["~/Downloads"],
  "mode": "plan|apply|undo|history",
  "sort_by": "type|extension|size|date|month|year",
  "destination": "~/Sorted",
  "recursive": true,
  "include": ["*.pdf"],
  "exclude": ["keep-*"],
  "rules": [{"pattern": "Screenshot*", "folder": "Screenshots"}],
  "categories": {"invoices": [".pdf"]},
  "conflict": "rename|skip|overwrite",
  "copy": false,
  "find_duplicates": true,
  "duplicates_action": "report|move",
  "remove_empty_dirs": true,
  "force": false,
  "manifest": "file-sort-20260929-111818-cd234b"
}
```

**Returns:**
- Status (success / partial-success / failed) and mode
- Summary, groups and per-status counts
- Operations (src → dst with status)
- Duplicate groups
- Organization report
- Plan: shell script artifact in `outgoing_patches/`
- Apply: undo manifest in `move_history/`
