"""Tests for the agent-builder code generator (fast: no dependency installs or packaging)."""

import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("agent_builder_runner", ROOT / "agent-builder" / "run_agent.py")
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)

TEMPLATE_IDS = sorted(builder.load_templates())


def test_templates_are_listed():
    result = builder.run({"mode": "templates"})
    assert result["status"] == "success"
    ids = {t["id"] for t in result["templates"]}
    assert {"web-static", "web-react", "desktop-tkinter", "desktop-electron", "game-html5", "game-pygame", "cli-python"} <= ids


@pytest.mark.parametrize(
    "goal, expected",
    [
        ("build a snake game exe", "game-pygame"),
        ("tetris in the browser", "game-html5"),
        ("react dashboard for sales", "web-react"),
        ("flask inventory app with database", "web-flask"),
        ("python api for orders", "api-fastapi"),
        ("windows exe that tracks my expenses", "desktop-tkinter"),
        ("electron app with installer", "desktop-electron"),
        ("command line tool to rename photos", "cli-python"),
        ("a landing page for my bakery", "web-static"),
    ],
)
def test_template_selection(goal, expected):
    assert builder.choose_template(goal, builder.load_templates())[0] == expected


def test_plan_is_a_dry_run(tmp_path):
    result = builder.run({"goal": "build a snake game exe", "targets": [str(tmp_path)]})
    assert result["status"] == "success"
    assert result["mode"] == "plan"
    assert result["project_name"] == "snake-game"
    assert "main.py" in result["files"]
    assert list(tmp_path.iterdir()) == []


def test_unknown_template_and_mode_fail():
    assert builder.run({"template": "nope", "mode": "plan"})["status"] == "failed"
    assert builder.run({"mode": "explode"})["status"] == "failed"


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_generate_every_template(tmp_path, template_id):
    result = builder.run({"goal": "Demo project", "template": template_id, "mode": "generate", "destination": str(tmp_path / "proj")})
    assert result["status"] == "success", result
    project = tmp_path / "proj"
    assert json.loads((project / ".agent-builder.json").read_text())["template"] == template_id
    assert (project / "README.md").is_file()

    for path in project.rglob("*"):
        if not path.is_file():
            continue
        assert "dot." not in path.name
        text = path.read_text(encoding="utf-8")
        for token in ("__APP_NAME__", "__APP_TITLE__", "__PKG_NAME__", "__APP_ID__", "__APP_DESCRIPTION__"):
            assert token not in text and token not in str(path), f"{token} left in {path}"
        if path.suffix == ".py":
            py_compile.compile(str(path), doraise=True, cfile=str(tmp_path / "x.pyc"))
        elif path.suffix == ".json":
            json.loads(text)
        elif path.suffix == ".js" and shutil.which("node"):
            subprocess.run(["node", "--check", str(path)], check=True, capture_output=True)


def test_generate_keeps_existing_files_unless_overwrite(tmp_path):
    dest = tmp_path / "site"
    dest.mkdir()
    (dest / "index.html").write_text("mine")
    task = {"goal": "site", "template": "web-static", "mode": "generate", "destination": str(dest)}

    result = builder.run(task)
    assert "index.html" in result["skipped"]
    assert (dest / "index.html").read_text() == "mine"

    result = builder.run({**task, "overwrite": True})
    assert "index.html" in result["written"]
    assert (dest / "index.html").read_text() != "mine"


def test_generated_cli_tests_pass(tmp_path):
    builder.run({"goal": "file stats", "template": "cli-python", "mode": "generate", "destination": str(tmp_path / "cli")})
    done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=tmp_path / "cli", capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_generated_tkinter_store_tests_pass(tmp_path):
    builder.run({"goal": "notes", "template": "desktop-tkinter", "mode": "generate", "destination": str(tmp_path / "desk")})
    done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=tmp_path / "desk", capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_build_requires_generated_project(tmp_path):
    result = builder.run({"mode": "build", "project": str(tmp_path)})
    assert result["status"] == "failed"
    assert ".agent-builder.json" in result["summary"]



# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.
