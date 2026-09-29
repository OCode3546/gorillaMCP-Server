"""File Sorter Agent - Organizes and categorizes files in workspace.

This agent discovers files in target directories and sorts/organizes them
by type, size, date, or custom criteria. Generates organization reports
and optional folder structure suggestions.

Exposes `run(task: dict) -> dict` function for MCP integration.
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import mimetypes

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "outgoing_patches")
os.makedirs(OUT_DIR, exist_ok=True)


# File type categories
FILE_CATEGORIES = {
    "code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".rs", ".go", ".rb", ".php", ".swift"],
    "markup": [".html", ".xml", ".md", ".tex", ".rst"],
    "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".env"],
    "style": [".css", ".scss", ".sass", ".less"],
    "data": [".csv", ".xlsx", ".xls", ".db", ".sqlite", ".sql"],
    "media": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".mp3", ".wav", ".flac"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
    "archive": [".zip", ".tar", ".gz", ".7z", ".rar"],
    "executable": [".exe", ".bin", ".app", ".sh", ".bat"],
}


def categorize_file(filepath: Path) -> str:
    """Categorize a file based on its extension."""
    ext = filepath.suffix.lower()
    
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    
    return "other"


def get_file_size_category(size_bytes: int) -> str:
    """Categorize file by size."""
    if size_bytes < 1024 * 100:  # < 100 KB
        return "small"
    elif size_bytes < 1024 * 1024 * 10:  # < 10 MB
        return "medium"
    else:
        return "large"


def get_date_category(filepath: Path) -> str:
    """Categorize file by modification date."""
    mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
    now = datetime.now()
    days_old = (now - mod_time).days
    
    if days_old == 0:
        return "today"
    elif days_old <= 7:
        return "this_week"
    elif days_old <= 30:
        return "this_month"
    elif days_old <= 365:
        return "this_year"
    else:
        return "older"


def discover_files(targets: List[str]) -> List[Dict[str, Any]]:
    """Discover all files in target directories."""
    files = []
    
    for target in targets:
        target_path = Path(target)
        
        if not target_path.exists():
            continue
        
        if target_path.is_file():
            files.append({
                "path": str(target_path),
                "name": target_path.name,
                "size": target_path.stat().st_size,
                "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat(),
            })
        elif target_path.is_dir():
            for filepath in target_path.rglob("*"):
                if filepath.is_file():
                    files.append({
                        "path": str(filepath),
                        "name": filepath.name,
                        "size": filepath.stat().st_size,
                        "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                    })
    
    return files


def sort_by_type(files: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Group files by type category."""
    grouped = {}
    
    for file_info in files:
        filepath = Path(file_info["path"])
        category = categorize_file(filepath)
        
        if category not in grouped:
            grouped[category] = []
        
        grouped[category].append(file_info)
    
    return grouped


def sort_by_date(files: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Group files by date modified."""
    grouped = {}
    
    for file_info in files:
        filepath = Path(file_info["path"])
        category = get_date_category(filepath)
        
        if category not in grouped:
            grouped[category] = []
        
        grouped[category].append(file_info)
    
    return grouped


def sort_by_size(files: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Group files by size category."""
    grouped = {}
    
    for file_info in files:
        filepath = Path(file_info["path"])
        size_cat = get_file_size_category(file_info["size"])
        
        if size_cat not in grouped:
            grouped[size_cat] = []
        
        grouped[size_cat].append(file_info)
    
    return grouped


def generate_report(files: List[Dict], grouped: Dict[str, List[Dict]], sort_by: str) -> str:
    """Generate a text report of file organization."""
    lines = [
        "=" * 70,
        "FILE ORGANIZATION REPORT",
        "=" * 70,
        f"Total files: {len(files)}",
        f"Sorted by: {sort_by}",
        "",
        "BREAKDOWN:",
        "",
    ]
    
    total_size = sum(f.get("size", 0) for f in files)
    
    for category, items in sorted(grouped.items()):
        category_size = sum(f.get("size", 0) for f in items)
        size_mb = category_size / (1024 * 1024)
        percentage = (category_size / total_size * 100) if total_size > 0 else 0
        
        lines.append(f"📁 {category.upper()}")
        lines.append(f"   Files: {len(items):>4} | Size: {size_mb:>8.2f} MB | {percentage:>5.1f}%")
        
        # Show first 5 files in category
        for file_info in items[:5]:
            filepath = Path(file_info["path"])
            size_kb = file_info.get("size", 0) / 1024
            lines.append(f"     - {filepath.name} ({size_kb:.1f} KB)")
        
        if len(items) > 5:
            lines.append(f"     ... and {len(items) - 5} more files")
        
        lines.append("")
    
    lines.extend([
        "=" * 70,
        f"Total Size: {total_size / (1024 * 1024):.2f} MB",
        "=" * 70,
    ])
    
    return "\n".join(lines)


def create_folder_structure_suggestions(grouped: Dict[str, List[Dict]]) -> List[str]:
    """Suggest folder structure based on grouping."""
    suggestions = []
    
    for category, items in grouped.items():
        if items:
            suggestions.append(f"mkdir -p './{category}'")
            for file_info in items:
                filepath = Path(file_info["path"])
                suggestions.append(f"# mv '{filepath}' './{category}/'")
    
    return suggestions


def create_patch(content: str) -> str:
    """Create a patch file with organization suggestions."""
    name = f"file-sort-{uuid.uuid4().hex[:8]}.patch"
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def run(task: Dict[str, Any]) -> Dict[str, Any]:
    """Main execution function for MCP integration."""
    goal = task.get("goal", "Sort and organize files")
    targets = task.get("targets", ["."])
    sort_by = task.get("sort_by", "type").lower()
    
    if sort_by not in ["type", "date", "size"]:
        sort_by = "type"
    
    # Discover files
    files = discover_files(targets)
    
    if not files:
        return {
            "status": "success",
            "summary": f"No files found in targets: {targets}",
            "files_found": 0,
            "plan": "No files to organize",
            "groups": {},
            "report": "No files found",
        }
    
    # Group files
    if sort_by == "type":
        grouped = sort_by_type(files)
    elif sort_by == "date":
        grouped = sort_by_date(files)
    else:  # size
        grouped = sort_by_size(files)
    
    # Generate report
    report = generate_report(files, grouped, sort_by)
    
    # Generate folder structure suggestions
    suggestions = create_folder_structure_suggestions(grouped)
    patch_content = "\n".join(suggestions)
    
    if patch_content.strip():
        patch_path = create_patch(patch_content)
    else:
        patch_path = None
    
    # Count total size
    total_size_mb = sum(f.get("size", 0) for f in files) / (1024 * 1024)
    
    return {
        "status": "success",
        "summary": f"Analyzed {len(files)} files across {len(grouped)} categories. Total size: {total_size_mb:.2f} MB",
        "plan": f"Organized files by {sort_by}. Generated grouping report and folder structure suggestions.",
        "files_found": len(files),
        "total_size_mb": round(total_size_mb, 2),
        "groups": {k: len(v) for k, v in grouped.items()},
        "report": report,
        "suggestions": suggestions[:20],  # First 20 suggestions
        "artifacts": [patch_path] if patch_path else [],
    }


def _cli_main():
    """CLI entry point for direct execution."""
    import argparse
    
    p = argparse.ArgumentParser(description="Run File Sorter Agent task")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-file", help="Path to JSON task file")
    group.add_argument("--task-json", help="Task JSON string")
    args = p.parse_args()
    
    if args.task_file:
        raw = open(args.task_file, "r", encoding="utf-8").read()
    else:
        raw = args.task_json
    
    task = json.loads(raw)
    result = run(task)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli_main()



# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.