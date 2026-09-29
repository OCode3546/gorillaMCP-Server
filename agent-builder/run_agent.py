"""Builder Agent - code generator that scaffolds complete, runnable projects.

Picks a project template from templates/ (web apps, APIs, desktop apps that
package to executables, games, CLIs), fills in the project name, writes the
files and can run the build (npm, vite, PyInstaller, electron-builder). The
generated project is a working starting point: the calling assistant then
customises it for the user's goal.

Modes:
- "plan" (default): dry run. Chooses a template and lists the files it would write.
- "generate" (alias "apply"): writes the project. Existing files are kept unless
  overwrite is set, and nothing is ever deleted.
- "build": installs dependencies and runs the template's build steps for a
  generated project (also triggered by generate with build=true).
- "templates": lists the available templates.

Exposes `run(task: dict) -> dict` function for MCP integration.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_OUTPUT_ROOT = BASE_DIR / "generated"
MARKER_FILE = ".agent-builder.json"
BUILD_STEP_TIMEOUT = 900  # seconds; npm/pip installs can be slow on a cold cache
MAX_OUTPUT_TAIL = 2000

# Words dropped when deriving a project name from the goal.
NAME_STOPWORDS = {
    "a", "an", "the", "me", "my", "i", "we", "our", "new", "simple", "basic", "small", "quick",
    "build", "create", "make", "generate", "scaffold", "write", "code", "want", "need", "please",
    "can", "could", "you", "that", "which", "to", "for", "with", "using", "in", "on", "of", "and",
    "as", "into", "from", "it", "is", "be", "some", "starter", "project", "app", "application",
    "exe", "executable", "windows", "mac", "macos", "linux", "desktop", "web", "webapp", "website",
    "python", "javascript", "js", "typescript", "node", "react", "vite", "flask", "fastapi",
    "electron", "pygame", "tkinter", "html", "html5", "cli", "gui", "api", "rest", "program",
    "tool", "utility", "command", "line", "terminal", "script", "installer", "browser",
}

VALID_MODES = {"plan", "generate", "apply", "build", "templates"}


# --------------------------------------------------------------------------- templates


def load_templates() -> dict[str, dict[str, Any]]:
    """Load every templates/<id>/template.json, keyed by template id."""
    templates: dict[str, dict[str, Any]] = {}
    if not TEMPLATES_DIR.is_dir():
        return templates
    for meta_path in sorted(TEMPLATES_DIR.glob("*/template.json")):
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["id"] = meta_path.parent.name
        meta["_files_dir"] = meta_path.parent / "files"
        templates[meta["id"]] = meta
    return templates


def _public_template(meta: dict[str, Any]) -> dict[str, Any]:
    keys = ("id", "title", "category", "description", "stack", "produces", "requires", "packages_executable")
    return {k: meta[k] for k in keys if k in meta}


def _keyword_hits(text: str, words: list[str]) -> list[str]:
    return [w for w in words if re.search(rf"\b{re.escape(w)}s?\b", text)]


def choose_template(goal: str, templates: dict[str, dict[str, Any]]) -> tuple[str, str, list[str]]:
    """Score templates against the goal. Returns (template_id, reason, alternatives).

    Strong keywords score 3 and hints score 1. Ties go to the lower "priority",
    which favours the zero-dependency templates.
    """
    text = goal.lower()
    scored = []
    for tid, meta in templates.items():
        strong = _keyword_hits(text, meta.get("keywords", []))
        hints = _keyword_hits(text, meta.get("hints", []))
        scored.append((3 * len(strong) + len(hints), -meta.get("priority", 50), tid, strong + hints))
    scored.sort(reverse=True)

    best_score, _, best_id, matched = scored[0]
    if best_score == 0:
        fallback = "web-static" if "web-static" in templates else best_id
        others = [tid for _, _, tid, _ in scored if tid != fallback][:3]
        return fallback, "No template keywords in the goal; defaulting to a static web app.", others
    alternatives = [tid for score, _, tid, _ in scored[1:4] if score > 0]
    return best_id, f"Matched: {', '.join(matched)}", alternatives


# --------------------------------------------------------------------------- naming


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "my-app"


def derive_name(goal: str, fallback: str) -> str:
    words = re.findall(r"[a-z0-9]+", goal.lower())
    kept = [w for w in words if w not in NAME_STOPWORDS]
    return "-".join(kept[:4]) or fallback


def make_tokens(name: str, title: str | None, description: str | None, goal: str) -> dict[str, str]:
    slug = slugify(name)
    pkg = slug.replace("-", "_")
    if pkg[0].isdigit():
        pkg = f"app_{pkg}"
    title = title or " ".join(part.capitalize() for part in slug.split("-"))
    return {
        "__APP_NAME__": slug,
        "__APP_TITLE__": title,
        "__PKG_NAME__": pkg,
        "__APP_ID__": f"com.example.{pkg.replace('_', '')}",
        "__APP_DESCRIPTION__": description or goal or f"{title}, generated by agent-builder",
        "__YEAR__": str(datetime.now().year),
    }


def _substitute(text: str, tokens: dict[str, str]) -> str:
    for key, value in tokens.items():
        text = text.replace(key, value)
    return text


# --------------------------------------------------------------------------- rendering


def render_files(meta: dict[str, Any], tokens: dict[str, str]) -> list[tuple[str, str]]:
    """Return (relative_path, content) for every template file with tokens filled in.

    Path parts named "dot.<x>" become ".<x>" so the templates' own .gitignore and
    .github folders don't take effect inside this workspace.
    """
    files_dir: Path = meta["_files_dir"]
    rendered = []
    for src in sorted(p for p in files_dir.rglob("*") if p.is_file()):
        if src.name == ".DS_Store" or "__pycache__" in src.parts:
            continue
        parts = [("." + p[4:]) if p.startswith("dot.") else p for p in src.relative_to(files_dir).parts]
        rel = _substitute("/".join(parts), tokens)
        rendered.append((rel, _substitute(src.read_text(encoding="utf-8"), tokens)))
    return rendered


def resolve_project_dir(task: dict[str, Any], name: str) -> Path:
    """destination is the exact project folder; otherwise <targets[0] or generated/>/<name>."""
    if task.get("destination"):
        return Path(os.path.expanduser(task["destination"])).resolve()
    targets = task.get("targets") or []
    parent = Path(os.path.expanduser(targets[0])).resolve() if targets else DEFAULT_OUTPUT_ROOT
    return parent / name


def write_project(project_dir: Path, files: list[tuple[str, str]], meta: dict[str, Any], tokens: dict[str, str], overwrite: bool) -> tuple[list[str], list[str]]:
    """Write files and the project marker. Returns (written, skipped)."""
    written, skipped = [], []
    for rel, content in files:
        dest = project_dir / rel
        if dest.exists() and not overwrite:
            skipped.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        if rel.endswith((".sh", ".command")):
            dest.chmod(0o755)
        written.append(rel)

    marker = {
        "generator": "agent-builder",
        "template": meta["id"],
        "name": tokens["__APP_NAME__"],
        "title": tokens["__APP_TITLE__"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (project_dir / MARKER_FILE).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    return written, skipped


# --------------------------------------------------------------------------- building


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "mac"
    return "linux"


def _venv_python(project_dir: Path) -> Path:
    if os.name == "nt":
        return project_dir / ".venv" / "Scripts" / "python.exe"
    return project_dir / ".venv" / "bin" / "python"


def _expand_cmd(cmd: list[str], project_dir: Path, tokens: dict[str, str]) -> list[str]:
    tools = {
        "{python}": sys.executable,
        "{venv_python}": str(_venv_python(project_dir)),
        "{npm}": shutil.which("npm") or "npm",
        "{node}": shutil.which("node") or "node",
    }
    return [_substitute(tools.get(part, part), tokens) for part in cmd]


def check_requirements(meta: dict[str, Any]) -> list[str]:
    # python3 is always present: this runner is Python.
    return [tool for tool in meta.get("requires", []) if tool != "python3" and shutil.which(tool) is None]


def run_build(project_dir: Path, meta: dict[str, Any], tokens: dict[str, str], env_overrides: dict[str, str] | None = None) -> dict[str, Any]:
    platform = _platform_key()
    env = {**os.environ, **meta.get("build_env", {}), **(env_overrides or {})}
    # Set by editor hosts such as VS Code; it makes Electron behave as plain Node.
    env.pop("ELECTRON_RUN_AS_NODE", None)
    steps_out = []
    ok = True
    for step in meta.get("build_steps", []):
        if step.get("platforms") and platform not in step["platforms"]:
            continue
        cmd = _expand_cmd(step["cmd"], project_dir, tokens)
        record: dict[str, Any] = {"name": step["name"], "command": " ".join(cmd)}
        try:
            done = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=BUILD_STEP_TIMEOUT, env=env)
            record["exit_code"] = done.returncode
            output = (done.stdout + ("\n" + done.stderr if done.stderr else "")).strip()
            record["output_tail"] = output[-MAX_OUTPUT_TAIL:]
        except FileNotFoundError as exc:
            record["exit_code"] = 127
            record["output_tail"] = str(exc)
        except subprocess.TimeoutExpired:
            record["exit_code"] = -1
            record["output_tail"] = f"Timed out after {BUILD_STEP_TIMEOUT}s"
        record["status"] = "success" if record["exit_code"] == 0 else "failed"
        steps_out.append(record)
        if record["status"] == "failed" and not step.get("optional"):
            ok = False
            break

    outputs = []
    for pattern in meta.get("build_outputs", []):
        outputs.extend(sorted(glob.glob(str(project_dir / _substitute(pattern, tokens)))))
    return {"ok": ok, "steps": steps_out, "outputs": outputs}


def _attach_build(result: dict[str, Any], project_dir: Path, meta: dict[str, Any], tokens: dict[str, str], task: dict[str, Any]) -> None:
    missing = check_requirements(meta)
    if missing:
        result["status"] = "failed"
        result["errors"].append(f"Cannot build: install {', '.join(missing)} first.")
        return
    build = run_build(project_dir, meta, tokens, task.get("env"))
    result["build"] = build
    result["artifacts"].extend(build["outputs"])
    if build["ok"]:
        result["summary"] += f" Build succeeded ({len(build['outputs'])} outputs)."
        return
    failed = next((s for s in build["steps"] if s["status"] == "failed"), None)
    result["status"] = "failed"
    result["errors"].append(f"Build step '{failed['name']}' failed; see build.steps[].output_tail." if failed else "Build failed.")
    result["summary"] += " Build failed."


# --------------------------------------------------------------------------- run


def _instructions(meta: dict[str, Any], key: str, tokens: dict[str, str]) -> list[str]:
    return [_substitute(line, tokens) for line in meta.get(key, [])]


def _platform_notes(meta: dict[str, Any], goal: str) -> list[str]:
    if not re.search(r"\b(exe|executable|windows|installer)\b", goal.lower()):
        return []
    if not meta.get("packages_executable"):
        return [f"Template '{meta['id']}' does not package to an executable; pick one with packages_executable (mode 'templates')."]
    if _platform_key() != "windows":
        return [
            "Executables are built for the OS the build runs on, so building here produces a "
            f"{_platform_key()} app, not a Windows .exe. For an .exe, build on Windows or push the project "
            "to GitHub: the included .github/workflows/build.yml builds Windows, macOS and Linux versions."
        ]
    return []


def run(task: dict[str, Any]) -> dict[str, Any]:
    goal = (task.get("goal") or "").strip()
    mode = (task.get("mode") or "plan").lower()
    templates = load_templates()

    if mode not in VALID_MODES:
        return {"status": "failed", "mode": mode, "summary": f"Unknown mode '{mode}'. Use one of: {', '.join(sorted(VALID_MODES))}."}
    if not templates:
        return {"status": "failed", "mode": mode, "summary": f"No templates found in {TEMPLATES_DIR}"}

    if mode == "templates":
        listing = [_public_template(m) for m in sorted(templates.values(), key=lambda m: m.get("priority", 50))]
        return {
            "status": "success",
            "mode": mode,
            "summary": f"{len(listing)} templates available.",
            "plan": "Pass one of these ids as `template`, or describe the project in `goal` to have one chosen.",
            "templates": listing,
        }

    if mode == "build":
        return _build_existing(task, templates)

    # plan / generate / apply
    warnings: list[str] = []
    requested = task.get("template")
    if requested:
        if requested not in templates:
            return {"status": "failed", "mode": mode, "summary": f"Unknown template '{requested}'. Available: {', '.join(sorted(templates))}."}
        template_id, reason, alternatives = requested, "Requested explicitly.", []
    else:
        template_id, reason, alternatives = choose_template(goal, templates)
        if reason.startswith("No template keywords"):
            warnings.append(reason)
    meta = templates[template_id]

    name = slugify(task.get("name") or derive_name(goal, meta.get("default_name", "my-app")))
    tokens = make_tokens(name, task.get("title"), task.get("description"), goal)
    project_dir = resolve_project_dir(task, tokens["__APP_NAME__"])
    files = render_files(meta, tokens)
    file_list = [rel for rel, _ in files]
    overwrite = bool(task.get("overwrite"))

    missing = check_requirements(meta)
    if missing:
        warnings.append(f"Missing tools needed to run/build this template: {', '.join(missing)}.")
    warnings.extend(_platform_notes(meta, goal))
    clashes = [rel for rel in file_list if (project_dir / rel).exists()]
    if clashes:
        warnings.append(
            f"{project_dir} already contains {len(clashes)} of these files; "
            + ("they will be overwritten." if overwrite else "they will be kept unless overwrite=true.")
        )

    plan = "\n".join(
        [
            f"Template: {meta['title']} ({template_id}). {reason}",
            f"Project: {tokens['__APP_TITLE__']} ({tokens['__APP_NAME__']})",
            f"Folder: {project_dir}",
            f"Files: {len(file_list)}",
            "Next: generate, customise the code for the goal, then build/run.",
        ]
    )
    result: dict[str, Any] = {
        "status": "success",
        "mode": mode,
        "goal": goal,
        "template": _public_template(meta),
        "template_reason": reason,
        "alternatives": alternatives,
        "project_name": tokens["__APP_NAME__"],
        "project_title": tokens["__APP_TITLE__"],
        "project_dir": str(project_dir),
        "files": file_list,
        "plan": plan,
        "run_instructions": _instructions(meta, "run", tokens),
        "build_instructions": _instructions(meta, "build", tokens),
        "customize": _instructions(meta, "customize", tokens),
        "artifacts": [],
        "warnings": warnings,
        "errors": [],
    }

    if mode == "plan":
        result["summary"] = (
            f"Dry run for '{goal or tokens['__APP_TITLE__']}': would generate a {meta['title']} project "
            f"with {len(file_list)} files in {project_dir}. Run again with mode='generate' to write it."
        )
        return result

    project_dir.mkdir(parents=True, exist_ok=True)
    written, skipped = write_project(project_dir, files, meta, tokens, overwrite)
    result["written"] = written
    result["skipped"] = skipped
    result["artifacts"] = [str(project_dir)]
    kept = f", {len(skipped)} existing kept" if skipped else ""
    result["summary"] = f"Generated {meta['title']} project '{tokens['__APP_TITLE__']}' in {project_dir} ({len(written)} files written{kept})."

    if task.get("build"):
        _attach_build(result, project_dir, meta, tokens, task)
    return result


def _build_existing(task: dict[str, Any], templates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    raw = task.get("project") or task.get("destination") or (task.get("targets") or [None])[0]
    if not raw:
        return {"status": "failed", "mode": "build", "summary": "Build needs `project` (or destination/targets) pointing at a generated project folder."}
    project_dir = Path(os.path.expanduser(raw)).resolve()
    marker_path = project_dir / MARKER_FILE
    if not marker_path.is_file():
        return {"status": "failed", "mode": "build", "summary": f"{project_dir} is not an agent-builder project (no {MARKER_FILE})."}
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    meta = templates.get(marker.get("template", ""))
    if meta is None:
        return {"status": "failed", "mode": "build", "summary": f"Template '{marker.get('template')}' from {MARKER_FILE} no longer exists."}

    tokens = make_tokens(marker["name"], marker.get("title"), None, "")
    result: dict[str, Any] = {
        "status": "success",
        "mode": "build",
        "template": _public_template(meta),
        "project_dir": str(project_dir),
        "plan": f"Run the {meta['title']} build steps in {project_dir}.",
        "summary": f"Build of '{tokens['__APP_TITLE__']}' ({meta['id']}).",
        "run_instructions": _instructions(meta, "run", tokens),
        "artifacts": [],
        "warnings": _platform_notes(meta, task.get("goal") or ""),
        "errors": [],
    }
    _attach_build(result, project_dir, meta, tokens, task)
    if "build" not in result and result["errors"]:
        result["summary"] = result["errors"][0]
    return result


def _cli_main():
    """CLI entry point for direct execution."""
    import argparse

    p = argparse.ArgumentParser(description="Run Builder Agent task")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-file", help="Path to JSON task file")
    group.add_argument("--task-json", help="Task JSON string")
    group.add_argument("--list-templates", action="store_true", help="List available project templates")
    args = p.parse_args()

    if args.list_templates:
        task = {"mode": "templates"}
    elif args.task_file:
        with open(args.task_file, "r", encoding="utf-8") as fh:
            task = json.load(fh)
    else:
        task = json.loads(args.task_json)
    print(json.dumps(run(task), indent=2))


if __name__ == "__main__":
    _cli_main()



# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.
