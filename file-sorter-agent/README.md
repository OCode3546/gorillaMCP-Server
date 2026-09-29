# File Sorter Agent — Complete Guide

An MCP agent that categorizes files and **actually moves them** into organized folders. It is safe by default: every run is a dry run until you ask it to apply, and every applied run can be undone.

## 🎯 What It Does

- **Plans** where every file should go (dry run, nothing touched)
- **Moves or copies** files into category folders when you apply
- **Undoes** any applied sort from its recorded manifest
- **Sorts by** type, extension, size, relative date, month, or year
- **Custom rules**: `Screenshot*` → `Screenshots/`, `invoice*.pdf` → `Finance/Invoices/`
- **Finds duplicates** by content hash, and can move extra copies to `duplicates/`
- **Cleans up** folders left empty after the move
- **Reports** size and file-count breakdowns per folder

## 🔁 Workflow: plan → apply → undo

```bash
cd file-sorter-agent

# 1. Dry run — shows what would move and writes a reviewable script
python run_agent.py --task-json '{"targets":["~/Downloads"],"recursive":false}'

# 2. Apply — really moves the files and records an undo manifest
python run_agent.py --task-json '{"targets":["~/Downloads"],"recursive":false}' --apply

# 3. Changed your mind? Undo the latest applied sort
python run_agent.py --undo

# List previous applied sorts (to undo a specific one: --undo <id>)
python run_agent.py --history
```

Result for a typical Downloads folder:

```text
Downloads/
├── archives/       project.zip
├── documents/      report.pdf, notes.txt
├── images/         photo.jpg, photo (1).jpg
├── installers/     Setup.dmg
├── Screenshots/    Screenshot 2026-09-29.png   ← custom rule
└── videos/         clip.mov
```

## 📋 File Categories (`sort_by: "type"`)

| Folder | Extensions |
|--------|-----------|
| **images** | .jpg .jpeg .png .gif .svg .webp .heic .psd … |
| **videos** | .mp4 .mov .avi .mkv .webm … |
| **audio** | .mp3 .wav .flac .aac .m4a … |
| **documents** | .pdf .doc .docx .txt .rtf .pages .epub |
| **spreadsheets** | .xlsx .xls .numbers .ods |
| **presentations** | .ppt .pptx .key .odp |
| **code** | .py .js .ts .java .go .rs .swift .ipynb … |
| **markup** | .html .xml .md .tex .rst |
| **config** | .json .yaml .toml .ini .env .plist |
| **style** | .css .scss .sass .less |
| **data** | .csv .tsv .db .sqlite .sql .parquet |
| **archives** | .zip .tar .gz .7z .rar |
| **installers** | .dmg .pkg .msi .deb .iso |
| **fonts** | .ttf .otf .woff .woff2 |
| **executables** | .exe .sh .bat .command |
| **other** | everything else |

Add or override categories with `"categories": {"invoices": [".pdf"]}`. Custom categories are checked first.

## 📊 Task Schema

```json
{
  "goal": "Sort my Downloads folder",
  "targets": ["~/Downloads"],
  "mode": "plan",
  "sort_by": "type",
  "destination": null,
  "recursive": true,
  "include": [],
  "exclude": [],
  "include_hidden": false,
  "rules": [{"pattern": "Screenshot*", "folder": "Screenshots"}],
  "categories": {},
  "conflict": "rename",
  "copy": false,
  "find_duplicates": false,
  "duplicates_action": "report",
  "remove_empty_dirs": false,
  "force": false
}
```

### Parameters

| Field | Default | Meaning |
|-------|---------|---------|
| **targets** | `["."]` | Folders (or single files) to sort |
| **mode** | `"plan"` | `plan` (dry run), `apply` (move files), `undo`, `history`. `"apply": true` also works |
| **sort_by** | `"type"` | `type`, `extension`, `size` (small/medium/large), `date` (today/this_week/…), `month` (`2026-09`), `year` |
| **destination** | each target | Root folder for the sorted folders. Use an absolute or `~` path |
| **recursive** | `true` | Also sort files in subfolders. Use `false` to sort only the top level |
| **include** / **exclude** | `[]` | Glob patterns matched against file name or relative path, e.g. `["*.pdf"]`, `["Projects/*"]` |
| **include_hidden** | `false` | Include dotfiles and dot-folders |
| **rules** | `[]` | Checked before `sort_by`, first match wins. Each rule has a `folder` plus any of `pattern` (glob), `extensions`, `name_contains`. Every condition given must match. `folder` may be nested: `"Finance/Invoices"` |
| **categories** | `{}` | Extra type categories: `{"folder": [".ext", …]}` |
| **conflict** | `"rename"` | When the destination exists: `rename` → `name (1).ext`, `skip`, or `overwrite` |
| **copy** | `false` | Copy instead of move (originals stay put) |
| **find_duplicates** | `false` | Hash file contents and report duplicate groups (the oldest copy is kept) |
| **duplicates_action** | `"report"` | `move` sends extra copies to `duplicates/` instead of their category |
| **remove_empty_dirs** | `false` | After moving, delete subfolders that are now empty |
| **force** | `false` | Required to apply inside a git repository |
| **manifest** | latest | For `undo`: run id or path of the manifest to revert |

## 🛡️ Safety

- **Dry run by default.** Nothing moves unless `mode` is `apply`.
- **Never overwrites** unless you set `conflict: "overwrite"`. Clashing names become `file (1).ext`, including two files from the same run.
- **Undo manifest.** Every applied run writes `move_history/<id>.json`. `undo` moves files back, restores removed folders, deletes folders the sort created, and refuses to undo twice. If a file's original spot is occupied by then, it is left where it is and reported.
- **Always skipped:** `.git`, `.venv`/`venv`, `node_modules`, `__pycache__` and other caches, hidden files, `.DS_Store`, app bundles (`.app`, `.photoslibrary`, …), symlinks, and partial downloads (`.crdownload`, `.part`, …).
- **Idempotent.** Files already inside their target folder are left alone, so running the same sort twice moves nothing.
- **Refused locations:** `/`, `/System`, `/Library`, `/Applications`, `/Users`, and a recursive sort of your whole home folder.
- **Git guard.** Applying inside a git repository fails unless `force: true`. Moving source files breaks code.

## 🔌 Via MCP

The `workspace-agent-registry` server exposes this agent through `run_agent_tool`. Put agent options in `extra`:

```json
{
  "agent_name": "file-sorter-agent",
  "goal": "Sort my Downloads folder",
  "targets": ["~/Downloads"],
  "extra": {"mode": "plan", "recursive": false, "find_duplicates": true}
}
```

Review the plan, then repeat with `"mode": "apply"`. To revert: `{"extra": {"mode": "undo"}}`.

## 🗂️ Recipes

### Downloads cleanup with screenshots and duplicates
```json
{
  "targets": ["~/Downloads"],
  "recursive": false,
  "rules": [{"pattern": "Screenshot*", "folder": "Screenshots"}],
  "duplicates_action": "move",
  "mode": "apply"
}
```

### Photos into year/month folders, copied to a new location
```json
{
  "targets": ["~/Pictures/Import"],
  "include": ["*.jpg", "*.jpeg", "*.heic", "*.png", "*.mov"],
  "sort_by": "month",
  "destination": "~/Pictures/Sorted",
  "copy": true,
  "mode": "apply"
}
```

### Invoices into a finance folder, everything else by extension
```json
{
  "targets": ["~/Documents/Inbox"],
  "sort_by": "extension",
  "rules": [{"name_contains": ["invoice", "factuur"], "extensions": ["pdf"], "folder": "Finance/Invoices"}]
}
```

### Flatten nested folders and clean up the empties
```json
{
  "targets": ["~/Desktop/Dump"],
  "remove_empty_dirs": true,
  "mode": "apply"
}
```

### Analysis only: what is using space?
```json
{"targets": ["./"], "sort_by": "size", "find_duplicates": true}
```

## 📈 Output Format

```json
{
  "status": "success",
  "mode": "apply",
  "summary": "Moved 7 of 8 files into 6 folders (1 already sorted, 0 skipped, 0 errors). Undo with mode='undo'.",
  "files_found": 8,
  "total_size_mb": 12.4,
  "groups": {"images": 3, "documents": 1, "Screenshots": 1},
  "counts": {"moved": 7, "in_place": 1},
  "operations": [{"src": ".../photo.jpg", "dst": ".../images/photo (1).jpg", "folder": "images", "status": "moved"}],
  "duplicates": [{"keep": ".../photo.jpg", "duplicates": [".../photo copy.jpg"], "wasted_bytes": 204800}],
  "report": "[text report]",
  "suggestions": ["mkdir -p ...", "mv -n ... ..."],
  "manifest": ".../move_history/file-sort-20260929-111818-cd234b.json",
  "artifacts": [".../move_history/file-sort-20260929-111818-cd234b.json"],
  "warnings": [],
  "errors": []
}
```

- **status**: `success`, `partial-success` (some operations failed), or `failed`
- **counts**: operations per status: `planned`, `moved`, `copied`, `in_place`, `skipped`, `error`
- **operations**: up to 200 non-trivial operations with source, destination and status
- **artifacts**: for a plan, a `.sh` script in `outgoing_patches/` (`mv -n` commands, safely quoted). For an apply, the undo manifest

---

**Tip:** Always look at the plan first. It is free, and the summary tells you exactly how many files will move where.
