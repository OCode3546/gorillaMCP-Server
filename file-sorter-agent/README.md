# File Sorter Agent — Complete Guide

A specialized MCP agent that intelligently categorizes, organizes, and sorts files in your workspace. Perfect for organizing code repositories, managing documentation, and understanding project structure.

## 🎯 What It Does

- **Categorizes files** by type (code, docs, media, configs, etc.)
- **Sorts by criteria**: file type, modification date, or file size
- **Generates reports**: detailed analysis of file organization
- **Creates suggestions**: folder structure and organization recommendations
- **Identifies patterns**: helps optimize workspace layout

## 📋 File Categories

The agent recognizes these file types:

| Category | Extensions | Examples |
|----------|-----------|----------|
| **Code** | .py, .js, .ts, .java, .cpp, etc. | Python, JavaScript, TypeScript |
| **Markup** | .html, .md, .xml, .tex | HTML, Markdown, XML |
| **Config** | .json, .yaml, .env, .toml | Configuration files |
| **Style** | .css, .scss, .less | Stylesheets |
| **Data** | .csv, .xlsx, .db, .sql | Data files |
| **Media** | .jpg, .mp4, .mp3, .wav | Images and media |
| **Document** | .pdf, .doc, .txt | Documents |
| **Archive** | .zip, .tar, .gz | Compressed files |
| **Executable** | .exe, .sh, .app | Executable files |
| **Other** | Everything else | Unknown types |

## 🚀 Quick Start

### Basic Usage

```bash
# Sort all files in src/ by type
python ~/Library/Application\ Support/Code/User/prompts/file-sorter-agent/run_agent.py \
  --task-json '{"goal":"Sort files by type","targets":["src/"],"sort_by":"type"}'
```

### Via MCP Server

```bash
# Using the MCP server tools
python mcp_server.py run_agent_tool file-sorter-agent \
  "Organize files in src/" \
  --targets='["src/"]'
```

## 📊 Task Schema

```json
{
  "goal": "Organize and analyze files",
  "targets": ["src/", "public/"],
  "sort_by": "type|date|size",
  "generate_report": true,
  "create_structure": true,
  "rules": {
    "group_by_extension": true,
    "create_subfolders": true,
    "pattern_rules": []
  }
}
```

### Parameters

- **goal** (string): What you want to accomplish
- **targets** (list): Directories/files to analyze
- **sort_by** (string): Sort criterion - "type", "date", or "size"
- **generate_report** (bool): Generate text report
- **create_structure** (bool): Suggest folder structure

## Use Cases

### 1. Organize a New Project
```json
{
  "goal": "Set up organized folder structure for new project",
  "targets": ["./"],
  "sort_by": "type"
}
```

**Output:** Categorizes all files by type and suggests folder creation

### 2. Find Large Files Taking Up Space
```json
{
  "goal": "Identify large files to optimize",
  "targets": ["./"],
  "sort_by": "size"
}
```

**Output:** Groups files by size (small, medium, large) with statistics

### 3. Identify Recently Modified Files
```json
{
  "goal": "Find files modified recently for backup",
  "targets": ["src/", "config/"],
  "sort_by": "date"
}
```

**Output:** Groups by modification date (today, this week, this month, etc.)

### 4. Analyze Media Files
```json
{
  "goal": "Organize media assets",
  "targets": ["assets/", "public/media/"],
  "sort_by": "type"
}
```

**Output:** Categorizes images, videos, audio files

## 📈 Output Format

The agent returns detailed analysis:

```json
{
  "status": "success",
  "summary": "Analyzed 150 files across 8 categories. Total size: 45.32 MB",
  "files_found": 150,
  "total_size_mb": 45.32,
  "groups": {
    "code": 42,
    "config": 18,
    "media": 35,
    "document": 12,
    "other": 43
  },
  "report": "[Full text report]",
  "suggestions": ["mkdir -p './code'", "mkdir -p './config'", ...],
  "artifacts": ["file-sort-abc12345.patch"]
}
```

### Fields

- **status**: "success" or "failed"
- **summary**: High-level overview
- **files_found**: Total number of files
- **total_size_mb**: Total disk usage
- **groups**: Count per category
- **report**: Formatted text report
- **suggestions**: Shell commands to create structure
- **artifacts**: Patch file with move commands

## 📝 Sample Report Output

```
======================================================================
FILE ORGANIZATION REPORT
======================================================================
Total files: 150
Sorted by: type

BREAKDOWN:

📁 CODE
   Files:   42 | Size:    25.30 MB | 55.8%
     - app.py (2.3 KB)
     - utils.py (4.1 KB)
     - models.py (8.7 KB)
     ... and 39 more files

📁 CONFIG
   Files:   18 | Size:     0.45 MB |  1.0%
     - package.json (1.2 KB)
     - .env (0.3 KB)
     ... and 16 more files

📁 MEDIA
   Files:   35 | Size:    15.20 MB | 33.5%
     - logo.png (250 KB)
     - banner.jpg (1.5 MB)
     ... and 33 more files

📁 DOCUMENT
   Files:   12 | Size:     3.60 MB |  7.9%
     - README.md (5.2 KB)
     - CONTRIBUTING.md (3.1 KB)
     ... and 10 more files

📁 OTHER
   Files:   43 | Size:     0.77 MB |  1.7%

======================================================================
Total Size: 45.32 MB
======================================================================
```

## 🔧 Advanced Examples

### Custom Sorting in CI/CD Pipeline
```bash
# Analyze workspace before deployment
python mcp_server.py run_agent_tool file-sorter-agent \
  "Pre-deployment file check" \
  --targets='["src/", "dist/"]' \
  --extra='{"sort_by":"size"}'
```

### Find Duplicates
```json
{
  "goal": "Identify potential duplicate files",
  "targets": ["src/", "tests/", "docs/"],
  "sort_by": "type"
}
```

Then review grouped files to spot duplicates by name.

## ✨ Real-World Scenarios

### Scenario 1: New Developer Joining Project
Developer wants to understand project structure:
```bash
python mcp_server.py run_agent_tool file-sorter-agent \
  "Help me understand this project structure" \
  --targets='["./"]'
```

Result: Clear breakdown of file types, what goes where, project size.

### Scenario 2: Storage Analysis
Need to clean up and free disk space:
```bash
python mcp_server.py run_agent_tool file-sorter-agent \
  "Find what's using most disk space" \
  --targets='["./"]' \
  --extra='{"sort_by":"size"}'
```

Result: Large files grouped for cleanup decisions.

### Scenario 3: Project Migration
Migrating from monolith to modular structure:
```bash
python mcp_server.py run_agent_tool file-sorter-agent \
  "Suggest folder structure for modular project" \
  --targets='["src/"]' \
  --extra='{"sort_by":"type","create_structure":true}'
```

Result: Organized structure suggestion with mkdir commands.

## 🎓 Tips & Tricks

1. **Combine with other agents**: Use results as input for code-errors agent
2. **Batch operations**: Run on multiple directories
3. **Automation**: Include in CI/CD pipelines for pre-deployment checks
4. **Reports**: Generate for documentation or team onboarding
5. **Size optimization**: Identify bloated directories

## 🔗 Integration with Other Agents

The File Sorter Agent works great with:
- **Code-Errors Agent**: Analyze errors in sorted code categories
- **Agent-Builder**: Use organization reports as build input
- **Manager Agent**: Route file organization tasks intelligently

## 📞 Output Usage

### Artifacts
The patch file contains shell commands to create suggested structure:
```bash
# Run the suggested commands
bash < file-sort-abc12345.patch
```

### Reports
Use in documentation:
```bash
# Extract just the report
python ... | jq -r '.report'
```

### Integration
Export for tooling:
```bash
# Get JSON for processing
python ... | jq '.groups' # Get group breakdown
```

---

**Ready to organize?** Use any of the examples above to get started!
