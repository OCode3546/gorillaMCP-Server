"""File Sorter Agent - Organizes and categorizes files in a workspace.

Discovers files in target directories, groups them by type, extension, size,
date or custom rules, and can actually move (or copy) them into category
folders. Every applied run writes a manifest so it can be undone.

Modes:
- "plan" (default): dry run. Reports what would move and writes a shell script.
- "apply": performs the moves and writes an undo manifest to move_history/.
- "undo": reverts a previous apply using its manifest (latest by default).
- "history": lists previous applied runs.

Exposes `run(task: dict) -> dict` function for MCP integration.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shlex
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "outgoing_patches")
HISTORY_DIR = os.path.join(BASE_DIR, "move_history")


# File type categories (folder name -> extensions)
FILE_CATEGORIES = {
    "images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".heic", ".heif", ".bmp", ".tiff", ".tif", ".ico", ".raw", ".cr2", ".nef", ".psd", ".ai"],
    "videos": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".aiff", ".wma"],
    "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".epub"],
    "spreadsheets": [".xlsx", ".xls", ".numbers", ".ods"],
    "presentations": [".ppt", ".pptx", ".key", ".odp"],
    "code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".rs", ".go", ".rb", ".php", ".swift", ".kt", ".scala", ".lua", ".r", ".ipynb"],
    "markup": [".html", ".htm", ".xml", ".md", ".tex", ".rst"],
    "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".cfg", ".env", ".plist"],
    "style": [".css", ".scss", ".sass", ".less"],
    "data": [".csv", ".tsv", ".db", ".sqlite", ".sql", ".parquet", ".jsonl"],
    "archives": [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar"],
    "installers": [".dmg", ".pkg", ".msi", ".deb", ".rpm", ".apk", ".iso"],
    "fonts": [".ttf", ".otf", ".woff", ".woff2"],
    "executables": [".exe", ".bin", ".sh", ".bat", ".command"],
}

# Directories never descended into: VCS metadata, environments and caches.
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".tox", ".idea", ".Trash",
}

# macOS package directories look like folders but must be treated as a single unit.
BUNDLE_SUFFIXES = {".app", ".bundle", ".framework", ".photoslibrary", ".xcodeproj", ".xcworkspace", ".plugin", ".kext"}

IGNORED_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "Icon\r"}

# Downloads still in progress; moving them would break the download.
PARTIAL_SUFFIXES = {".crdownload", ".part", ".partial", ".download", ".opdownload", ".tmp"}

SORT_OPTIONS = ("type", "extension", "size", "date", "month", "year")
CONFLICT_OPTIONS = ("rename", "skip", "overwrite")

# Paths where applying moves is always refused.
PROTECTED_PATHS = {Path(p) for p in ("/", "/System", "/Library", "/Applications", "/Users", "/usr", "/bin", "/etc", "/private")}

MAX_LISTED_OPERATIONS = 200


def categorize_file(filepath: Path, categories: dict[str, list[str]] | None = None) -> str:
    """Categorize a file based on its extension."""
    ext = filepath.suffix.lower()

    for category, extensions in (categories or FILE_CATEGORIES).items():
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


def get_date_category(mtime: float) -> str:
    """Categorize file by how long ago it was modified."""
    days_old = (datetime.now() - datetime.fromtimestamp(mtime)).days

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


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _normalize_ext(ext: str) -> str:
    ext = str(ext).lower()
    return ext if ext.startswith(".") else f".{ext}"


def parse_options(task: dict[str, Any]) -> dict[str, Any]:
    """Normalize task fields into the options used by the planner."""
    mode = str(task.get("mode") or "").lower()
    if not mode:
        mode = "apply" if task.get("apply") is True or task.get("dry_run") is False else "plan"

    sort_by = str(task.get("sort_by", "type")).lower()
    if sort_by not in SORT_OPTIONS:
        sort_by = "type"

    conflict = str(task.get("conflict", "rename")).lower()
    if conflict not in CONFLICT_OPTIONS:
        conflict = "rename"

    # Custom categories are checked before the built-in ones so they can override them.
    categories: dict[str, list[str]] = {
        name: [_normalize_ext(e) for e in _as_list(exts)] for name, exts in (task.get("categories") or {}).items()
    }
    categories.update({k: v for k, v in FILE_CATEGORIES.items() if k not in categories})

    # `rules` may be a list of rules or the legacy {"pattern_rules": [...]} dict.
    raw_rules = task.get("rules") or []
    if isinstance(raw_rules, dict):
        raw_rules = raw_rules.get("pattern_rules") or []
    rules = [r for r in raw_rules if isinstance(r, dict) and r.get("folder")]

    destination = task.get("destination")
    duplicates_action = "move" if task.get("duplicates_action") == "move" else "report"

    return {
        "mode": mode,
        "goal": task.get("goal", "Sort and organize files"),
        "targets": _as_list(task.get("targets")) or ["."],
        "sort_by": sort_by,
        "destination": str(Path(destination).expanduser().resolve()) if destination else None,
        "recursive": bool(task.get("recursive", True)),
        "include": _as_list(task.get("include")),
        "exclude": _as_list(task.get("exclude")),
        "include_hidden": bool(task.get("include_hidden", False)),
        "categories": categories,
        "rules": rules,
        "conflict": conflict,
        "copy": bool(task.get("copy", False)),
        "find_duplicates": bool(task.get("find_duplicates", False)) or duplicates_action == "move",
        "duplicates_action": duplicates_action,
        "remove_empty_dirs": bool(task.get("remove_empty_dirs", False)),
        "force": bool(task.get("force", False)),
        "generate_report": bool(task.get("generate_report", True)),
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _matches_any(name: str, rel: str, patterns: list[str]) -> bool:
    name, rel = name.lower(), rel.lower()
    return any(fnmatch.fnmatch(name, p.lower()) or fnmatch.fnmatch(rel, p.lower()) for p in patterns)


def _keep_dir(dirpath: str, name: str, root: str, opts: dict[str, Any]) -> bool:
    full = os.path.join(dirpath, name)
    if name in EXCLUDED_DIRS or Path(name).suffix.lower() in BUNDLE_SUFFIXES:
        return False
    if name.startswith(".") and not opts["include_hidden"]:
        return False
    if full in (OUT_DIR, HISTORY_DIR):
        return False
    return not _matches_any(name, os.path.relpath(full, root), opts["exclude"])


def _keep_file(path: Path, root: str, opts: dict[str, Any]) -> bool:
    name = path.name
    if name in IGNORED_FILENAMES or path.suffix.lower() in PARTIAL_SUFFIXES:
        return False
    if name.startswith(".") and not opts["include_hidden"]:
        return False
    if path.is_symlink() or not path.is_file():
        return False
    rel = os.path.relpath(path, root)
    if opts["exclude"] and _matches_any(name, rel, opts["exclude"]):
        return False
    if opts["include"] and not _matches_any(name, rel, opts["include"]):
        return False
    return True


def _file_info(path: Path, root: str) -> dict[str, Any]:
    st = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "size": st.st_size,
        "mtime": st.st_mtime,
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "root": root,
    }


def discover_files(targets: list[str], opts: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Discover files in target directories. Returns (files, warnings)."""
    opts = opts or parse_options({"targets": targets})
    files: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for target in targets:
        target_path = Path(target).expanduser().resolve()

        if not target_path.exists():
            warnings.append(f"Target does not exist: {target}")
            continue

        if target_path.is_file():
            root = str(target_path.parent)
            if str(target_path) not in seen and _keep_file(target_path, root, opts):
                seen.add(str(target_path))
                files.append(_file_info(target_path, root))
            continue

        root = str(target_path)
        for dirpath, dirnames, filenames in os.walk(root):
            if opts["recursive"]:
                dirnames[:] = sorted(d for d in dirnames if _keep_dir(dirpath, d, root, opts))
            else:
                dirnames[:] = []
            for filename in sorted(filenames):
                path = Path(dirpath) / filename
                if str(path) in seen or not _keep_file(path, root, opts):
                    continue
                seen.add(str(path))
                files.append(_file_info(path, root))

    return files, warnings


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _match_rule(file_info: dict[str, Any], rule: dict[str, Any]) -> bool:
    """A rule matches when every condition it sets (pattern, extensions, name_contains) matches."""
    name = file_info["name"].lower()
    patterns = [p.lower() for p in _as_list(rule.get("pattern"))]
    extensions = [_normalize_ext(e) for e in _as_list(rule.get("extensions"))]
    contains = [c.lower() for c in _as_list(rule.get("name_contains"))]
    if not (patterns or extensions or contains):
        return False
    if patterns and not any(fnmatch.fnmatch(name, p) for p in patterns):
        return False
    if extensions and Path(name).suffix not in extensions:
        return False
    if contains and not any(c in name for c in contains):
        return False
    return True


def classify(file_info: dict[str, Any], opts: dict[str, Any]) -> str:
    """Return the destination folder (relative) for a file."""
    for rule in opts["rules"]:
        if _match_rule(file_info, rule):
            return str(rule["folder"])

    sort_by = opts["sort_by"]
    if sort_by == "extension":
        return Path(file_info["name"]).suffix.lower().lstrip(".") or "no_extension"
    if sort_by == "size":
        return get_file_size_category(file_info["size"])
    if sort_by == "date":
        return get_date_category(file_info["mtime"])
    if sort_by == "month":
        return datetime.fromtimestamp(file_info["mtime"]).strftime("%Y-%m")
    if sort_by == "year":
        return datetime.fromtimestamp(file_info["mtime"]).strftime("%Y")
    return categorize_file(Path(file_info["name"]), opts["categories"])


def group_files(files: list[dict[str, Any]], opts: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for file_info in files:
        grouped.setdefault(classify(file_info, opts), []).append(file_info)
    return grouped


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------

def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find files with identical content. The oldest copy in each group is the keeper."""
    by_size: dict[int, list[dict[str, Any]]] = {}
    for f in files:
        if f["size"] > 0:
            by_size.setdefault(f["size"], []).append(f)

    groups: list[dict[str, Any]] = []
    for same_size in by_size.values():
        if len(same_size) < 2:
            continue
        by_hash: dict[str, list[dict[str, Any]]] = {}
        for f in same_size:
            try:
                by_hash.setdefault(_sha256(f["path"]), []).append(f)
            except OSError:
                continue
        for digest, same in by_hash.items():
            if len(same) < 2:
                continue
            same.sort(key=lambda f: (f["mtime"], f["path"]))
            groups.append({
                "hash": digest,
                "size": same[0]["size"],
                "keep": same[0]["path"],
                "duplicates": [f["path"] for f in same[1:]],
                "wasted_bytes": same[0]["size"] * (len(same) - 1),
            })

    groups.sort(key=lambda g: g["wasted_bytes"], reverse=True)
    return groups


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def _unique_path(path: Path, taken: set[str]) -> Path:
    """Return `path`, or `name (n).ext` if it already exists or is reserved by the plan."""
    if not path.exists() and str(path) not in taken:
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists() and str(candidate) not in taken:
            return candidate
        n += 1


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def build_plan(files: list[dict[str, Any]], opts: dict[str, Any], duplicates: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Work out where every file should go without touching the filesystem."""
    dup_paths: set[str] = set()
    if duplicates and opts["duplicates_action"] == "move":
        dup_paths = {p for g in duplicates for p in g["duplicates"]}

    taken: set[str] = set()
    ops: list[dict[str, Any]] = []
    for file_info in files:
        src = Path(file_info["path"])
        folder = "duplicates" if file_info["path"] in dup_paths else classify(file_info, opts)
        target_dir = Path(opts["destination"] or file_info["root"]) / folder
        op = {"src": str(src), "folder": folder}

        # Files already somewhere inside their target folder stay put (keeps re-runs idempotent).
        if _is_within(src.parent, target_dir):
            ops.append({**op, "dst": str(src), "status": "in_place"})
            continue

        dst = target_dir / src.name
        if dst.exists() or str(dst) in taken:
            if opts["conflict"] == "skip":
                ops.append({**op, "dst": str(dst), "status": "skipped", "reason": "destination exists"})
                continue
            # Overwrite only clobbers pre-existing files, never another file from this same run.
            if opts["conflict"] == "rename" or str(dst) in taken:
                dst = _unique_path(dst, taken)

        taken.add(str(dst))
        ops.append({**op, "dst": str(dst), "status": "planned"})
    return ops


def build_script(ops: list[dict[str, Any]], opts: dict[str, Any]) -> str:
    """Render the plan as a reviewable shell script."""
    verb = "cp -p" if opts["copy"] else "mv"
    no_clobber = "" if opts["conflict"] == "overwrite" else " -n"
    lines = [
        "#!/bin/sh",
        f"# File Sorter plan generated {datetime.now().isoformat(timespec='seconds')}",
        f"# Goal: {opts['goal']}",
        "# Review before running. Prefer running the agent with mode=apply: it records an undo manifest.",
        "",
    ]
    made: set[str] = set()
    for op in ops:
        if op["status"] != "planned":
            continue
        parent = str(Path(op["dst"]).parent)
        if parent not in made:
            made.add(parent)
            lines.append(f"mkdir -p {shlex.quote(parent)}")
        lines.append(f"{verb}{no_clobber} {shlex.quote(op['src'])} {shlex.quote(op['dst'])}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Applying and undoing
# ---------------------------------------------------------------------------

def _in_git_repo(path: Path) -> bool:
    return any((p / ".git").exists() for p in (path, *path.parents))


def safety_problems(opts: dict[str, Any]) -> list[str]:
    """Reasons an apply should be refused."""
    problems = []
    roots = [Path(t).expanduser().resolve() for t in opts["targets"]]
    if opts["destination"]:
        roots.append(Path(opts["destination"]))
    home = Path.home().resolve()
    for root in roots:
        if root in PROTECTED_PATHS:
            problems.append(f"Refusing to reorganize system path {root}.")
        elif root == home and opts["recursive"]:
            problems.append("Refusing to recursively reorganize the whole home folder; target a subfolder or set recursive=false.")
        elif _in_git_repo(root) and not opts["force"]:
            problems.append(f"{root} is inside a git repository and moving files can break code; set force=true to proceed anyway.")
    return problems


def _remove_empty_dir(path: Path) -> bool:
    """Remove `path` if it holds nothing but OS junk files like .DS_Store."""
    try:
        children = list(path.iterdir())
        if any(child.name not in IGNORED_FILENAMES for child in children):
            return False
        for child in children:
            child.unlink()
        path.rmdir()
        return True
    except OSError:
        return False


def _write_manifest(manifest: dict[str, Any]) -> str:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, f"{manifest['id']}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return path


def apply_plan(ops: list[dict[str, Any]], opts: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """Execute planned operations. Returns (updated ops, manifest path)."""
    manifest: dict[str, Any] = {
        "id": f"file-sort-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "goal": opts["goal"],
        "targets": opts["targets"],
        "copy": opts["copy"],
        "operations": [],
        "created_dirs": [],
        "removed_dirs": [],
    }
    reserved = {op["dst"] for op in ops if op["status"] == "planned"}
    action = "copy" if opts["copy"] else "move"
    try:
        for op in ops:
            if op["status"] != "planned":
                continue
            src, dst = Path(op["src"]), Path(op["dst"])
            try:
                if not src.exists():
                    op.update(status="error", reason="source no longer exists")
                    continue
                # Something may have appeared at the destination since planning.
                if dst.exists() and opts["conflict"] != "overwrite":
                    if opts["conflict"] == "skip":
                        op.update(status="skipped", reason="destination exists")
                        continue
                    dst = _unique_path(dst, reserved - {str(dst)})
                    reserved.add(str(dst))
                    op["dst"] = str(dst)

                missing = [p for p in (dst.parent, *dst.parent.parents) if not p.exists()]
                dst.parent.mkdir(parents=True, exist_ok=True)
                manifest["created_dirs"].extend(str(p) for p in reversed(missing))

                if opts["copy"]:
                    shutil.copy2(src, dst)
                else:
                    shutil.move(str(src), str(dst))
                op["status"] = "copied" if opts["copy"] else "moved"
                manifest["operations"].append({"src": str(src), "dst": str(dst), "action": action})
            except OSError as exc:
                op.update(status="error", reason=str(exc))

        if opts["remove_empty_dirs"] and not opts["copy"]:
            roots = {Path(t).expanduser().resolve() for t in opts["targets"]}
            candidates = {Path(op["src"]).parent for op in ops if op["status"] == "moved"}
            # Deepest first so emptied parents can be removed after their children.
            for directory in sorted(candidates, key=lambda p: len(p.parts), reverse=True):
                current = directory
                while current not in roots and any(_is_within(current, r) for r in roots):
                    if not _remove_empty_dir(current):
                        break
                    manifest["removed_dirs"].append(str(current))
                    current = current.parent
    finally:
        # Written even if something above raised, so partial runs can still be undone.
        manifest_path = _write_manifest(manifest) if manifest["operations"] or manifest["removed_dirs"] else None

    return ops, manifest_path


def _load_manifests() -> list[tuple[str, dict[str, Any]]]:
    manifests = []
    if os.path.isdir(HISTORY_DIR):
        for name in os.listdir(HISTORY_DIR):
            if not name.endswith(".json"):
                continue
            path = os.path.join(HISTORY_DIR, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    manifests.append((path, json.load(fh)))
            except (OSError, json.JSONDecodeError):
                continue
    manifests.sort(key=lambda item: (item[1].get("created_at") or "", item[0]), reverse=True)
    return manifests


def undo(task: dict[str, Any]) -> dict[str, Any]:
    """Revert a previous apply using its manifest."""
    ref = task.get("manifest")
    if ref:
        path = ref if os.path.isfile(ref) else os.path.join(HISTORY_DIR, ref if ref.endswith(".json") else f"{ref}.json")
    else:
        path = next((p for p, m in _load_manifests() if not m.get("undone_at") and m.get("operations")), None)
    if not path or not os.path.isfile(path):
        return {"status": "failed", "mode": "undo", "summary": f"No manifest found to undo ({ref or 'no applied runs left in history'})."}

    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("undone_at"):
        return {"status": "failed", "mode": "undo", "summary": f"{manifest['id']} was already undone at {manifest['undone_at']}.", "manifest": path}

    for directory in sorted(manifest.get("removed_dirs", []), key=lambda p: len(Path(p).parts)):
        Path(directory).mkdir(parents=True, exist_ok=True)

    restored, problems = 0, []
    for entry in reversed(manifest.get("operations", [])):
        src, dst = Path(entry["src"]), Path(entry["dst"])
        try:
            if entry["action"] == "copy":
                if dst.exists():
                    dst.unlink()
                    restored += 1
            elif not dst.exists():
                problems.append(f"missing, cannot restore: {dst}")
            elif src.exists():
                problems.append(f"original location is occupied, left in place: {dst}")
            else:
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                restored += 1
        except OSError as exc:
            problems.append(f"{dst}: {exc}")

    removed_dirs = 0
    for directory in sorted(manifest.get("created_dirs", []), key=lambda p: len(Path(p).parts), reverse=True):
        if Path(directory).is_dir() and _remove_empty_dir(Path(directory)):
            removed_dirs += 1

    manifest["undone_at"] = datetime.now().isoformat(timespec="seconds")
    manifest["undo_problems"] = problems
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    total = len(manifest.get("operations", []))
    return {
        "status": "success" if not problems else ("partial-success" if restored else "failed"),
        "mode": "undo",
        "summary": f"Restored {restored}/{total} files from {manifest['id']} and removed {removed_dirs} folders the sort had created.",
        "restored": restored,
        "errors": problems,
        "manifest": path,
        "artifacts": [path],
    }


def list_history(limit: int = 20) -> dict[str, Any]:
    runs = [
        {
            "id": m.get("id"),
            "created_at": m.get("created_at"),
            "goal": m.get("goal"),
            "files": len(m.get("operations", [])),
            "undone_at": m.get("undone_at"),
            "manifest": path,
        }
        for path, m in _load_manifests()
    ]
    return {"status": "success", "mode": "history", "summary": f"{len(runs)} recorded sort runs.", "runs": runs[:limit]}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _fmt_size(size: float) -> str:
    if size < 1024:
        return f"{int(size)} B"
    for unit in ("KB", "MB", "GB"):
        size /= 1024
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
    return f"{size:.1f} GB"


def _count_statuses(ops: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for op in ops:
        counts[op["status"]] = counts.get(op["status"], 0) + 1
    return counts


def generate_report(files: list[dict], grouped: dict[str, list[dict]], sort_by: str,
                    ops: list[dict[str, Any]] | None = None, duplicates: list[dict[str, Any]] | None = None,
                    mode: str = "plan") -> str:
    """Generate a text report of file organization."""
    lines = [
        "=" * 70,
        "FILE ORGANIZATION REPORT",
        "=" * 70,
        f"Total files: {len(files)}",
        f"Sorted by: {sort_by}",
        f"Mode: {mode}",
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

        # Show the 5 largest files in category
        for file_info in sorted(items, key=lambda f: f.get("size", 0), reverse=True)[:5]:
            lines.append(f"     - {file_info['name']} ({_fmt_size(file_info.get('size', 0))})")

        if len(items) > 5:
            lines.append(f"     ... and {len(items) - 5} more files")

        lines.append("")

    if ops is not None:
        counts = _count_statuses(ops)
        verb = "would move" if mode == "plan" else "moved"
        lines.extend([
            "OPERATIONS:",
            f"   {verb}: {counts.get('planned', 0) + counts.get('moved', 0) + counts.get('copied', 0)}"
            f" | already sorted: {counts.get('in_place', 0)}"
            f" | skipped: {counts.get('skipped', 0)} | errors: {counts.get('error', 0)}",
            "",
        ])

    if duplicates:
        wasted = sum(g["wasted_bytes"] for g in duplicates)
        lines.append(f"DUPLICATES: {len(duplicates)} groups, {_fmt_size(wasted)} reclaimable")
        for group in duplicates[:5]:
            lines.append(f"   keep {Path(group['keep']).name} ({_fmt_size(group['size'])}), {len(group['duplicates'])} extra copies")
        lines.append("")

    lines.extend([
        "=" * 70,
        f"Total Size: {total_size / (1024 * 1024):.2f} MB",
        "=" * 70,
    ])

    return "\n".join(lines)


def create_script(content: str) -> str:
    """Write the plan's shell script to outgoing_patches/."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"file-sort-{uuid.uuid4().hex[:8]}.sh")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, 0o755)
    return path


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run(task: dict[str, Any]) -> dict[str, Any]:
    """Main execution function for MCP integration."""
    opts = parse_options(task)

    if opts["mode"] == "undo":
        return undo(task)
    if opts["mode"] == "history":
        return list_history()
    if opts["mode"] not in ("plan", "apply"):
        return {"status": "failed", "mode": opts["mode"], "summary": f"Unknown mode '{opts['mode']}'. Use plan, apply, undo or history."}

    # Checked before scanning so protected locations are never even walked.
    if opts["mode"] == "apply":
        problems = safety_problems(opts)
        if problems:
            return {
                "status": "failed",
                "mode": "apply",
                "summary": "Nothing was moved. " + " ".join(problems),
                "errors": problems,
            }

    files, warnings = discover_files(opts["targets"], opts)

    if not files:
        return {
            "status": "success",
            "mode": opts["mode"],
            "summary": f"No files found in targets: {opts['targets']}",
            "files_found": 0,
            "plan": "No files to organize",
            "groups": {},
            "report": "No files found",
            "warnings": warnings,
        }

    if opts["mode"] == "plan" and any(_in_git_repo(Path(t).expanduser().resolve()) for t in opts["targets"]):
        warnings.append("Target is inside a git repository; applying will require force=true.")

    duplicates = find_duplicates(files) if opts["find_duplicates"] else []
    grouped = group_files(files, opts)
    ops = build_plan(files, opts, duplicates)

    artifacts: list[str] = []
    manifest_path = None
    if opts["mode"] == "apply":
        ops, manifest_path = apply_plan(ops, opts)
        if manifest_path:
            artifacts.append(manifest_path)

    script = build_script(ops, opts)
    if opts["mode"] == "plan" and any(op["status"] == "planned" for op in ops):
        artifacts.append(create_script(script))

    counts = _count_statuses(ops)
    total_size_mb = sum(f.get("size", 0) for f in files) / (1024 * 1024)
    report = generate_report(files, grouped, opts["sort_by"], ops, duplicates, opts["mode"]) if opts["generate_report"] else ""
    verb = "copied" if opts["copy"] else "moved"

    if opts["mode"] == "plan":
        summary = (f"Dry run: {counts.get('planned', 0)} of {len(files)} files would be {verb} "
                   f"into {len(grouped)} folders ({counts.get('in_place', 0)} already sorted, {counts.get('skipped', 0)} skipped). "
                   f"Run again with mode='apply' to do it.")
    else:
        done = counts.get("moved", 0) + counts.get("copied", 0)
        summary = (f"{verb.capitalize()} {done} of {len(files)} files into {len(grouped)} folders "
                   f"({counts.get('in_place', 0)} already sorted, {counts.get('skipped', 0)} skipped, "
                   f"{counts.get('error', 0)} errors). Undo with mode='undo'.")
    if duplicates:
        summary += f" Found {len(duplicates)} groups of duplicate files."

    errors = [f"{op['src']}: {op['reason']}" for op in ops if op["status"] == "error"]
    status = "success"
    if errors:
        status = "partial-success" if counts.get("moved") or counts.get("copied") else "failed"

    return {
        "status": status,
        "mode": opts["mode"],
        "summary": summary,
        "plan": f"Sort files by {opts['sort_by']}"
                + (f" with {len(opts['rules'])} custom rules" if opts["rules"] else "")
                + f" into {opts['destination'] or 'each target folder'}.",
        "files_found": len(files),
        "total_size_mb": round(total_size_mb, 2),
        "groups": {k: len(v) for k, v in grouped.items()},
        "counts": counts,
        "operations": [op for op in ops if op["status"] != "in_place"][:MAX_LISTED_OPERATIONS],
        "duplicates": duplicates[:20],
        "report": report,
        "suggestions": [line for line in script.splitlines() if line and not line.startswith("#")][:20],
        "manifest": manifest_path,
        "artifacts": artifacts,
        "warnings": warnings,
        "errors": errors,
    }


def _cli_main():
    """CLI entry point for direct execution."""
    import argparse

    p = argparse.ArgumentParser(description="Run File Sorter Agent task")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-file", help="Path to JSON task file")
    group.add_argument("--task-json", help="Task JSON string")
    group.add_argument("--undo", nargs="?", const="", metavar="MANIFEST", help="Undo the latest (or the given) applied sort")
    group.add_argument("--history", action="store_true", help="List previous applied sorts")
    p.add_argument("--apply", action="store_true", help="Actually move files (the default is a dry run)")
    args = p.parse_args()

    if args.undo is not None:
        task = {"mode": "undo", "manifest": args.undo or None}
    elif args.history:
        task = {"mode": "history"}
    else:
        if args.task_file:
            with open(args.task_file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = args.task_json
        task = json.loads(raw)
        if args.apply:
            task["mode"] = "apply"

    result = run(task)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli_main()



# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.
