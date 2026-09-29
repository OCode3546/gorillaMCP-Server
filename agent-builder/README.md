# Builder Agent: code generator

Generates complete, runnable starter projects from a one-line goal and can build them into deployable output: a static site, a production bundle, an installer, or a standalone executable.

The agent is deterministic and offline. It picks a template, fills in the project name and writes working, tested code. The assistant calling it (Claude via the `/agent-builder` skill or the MCP tools) then customises that code for the actual goal: game rules, screens, data model, and so on.

## Templates

| Template | What you get | Output |
| --- | --- | --- |
| `web-static` | HTML/CSS/JS app, no dependencies | Static site |
| `web-react` | React + Vite single-page app | `dist/` bundle |
| `web-flask` | Flask + SQLite full-stack app with JSON API and tests | Python web server |
| `api-fastapi` | FastAPI REST service with Pydantic models, tests, Dockerfile | HTTP API |
| `desktop-tkinter` | Python desktop GUI (standard library only) with tests | `.exe` / `.app` / Linux binary via PyInstaller |
| `desktop-electron` | Electron app with secure preload/IPC | Windows installer + portable `.exe`, `.dmg`, AppImage |
| `game-html5` | Canvas arcade game with states, levels, lives, high score | Browser game |
| `game-pygame` | The same game in pygame-ce, with a headless smoke test | `.exe` / `.app` / Linux binary via PyInstaller |
| `cli-python` | Installable CLI with subcommands, JSON output and tests | pip package + single-file executable |

Run `python run_agent.py --list-templates` for the full metadata.

## Usage

```bash
# 1. Dry run: which template, where, which files
python run_agent.py --task-json '{"goal": "build a snake game exe"}'

# 2. Write the project (default location: agent-builder/generated/<name>)
python run_agent.py --task-json '{"goal": "build a snake game exe", "mode": "generate"}'

# 3. Install dependencies, run tests and package
python run_agent.py --task-json '{"mode": "build", "project": "generated/snake-game"}'
```

Useful fields: `template` (skip auto-selection), `name`, `title`, `description`, `destination` (exact folder, e.g. `~/Projects/snake`), `overwrite`, and `build: true` (build straight after generating).

Through MCP: `run_agent_tool(agent_name="agent-builder", goal="...", extra={"mode": "generate"})`.

## About executables

PyInstaller and electron-builder build for the OS they run on, so a Mac produces a `.app`/`.dmg`, not a Windows `.exe`. Every template that packages to an executable includes:

- `build_exe.bat` (Python templates) or `npm run dist:win` (Electron) to run on Windows
- `.github/workflows/build.yml`, which builds Windows, macOS and Linux versions on GitHub Actions

## Adding a template

1. Create `templates/<id>/files/` with the project files. Use these tokens in file contents or paths: `__APP_NAME__` (kebab-case), `__APP_TITLE__`, `__PKG_NAME__` (snake_case), `__APP_ID__`, `__APP_DESCRIPTION__`, `__YEAR__`. Name dotfiles `dot.gitignore` / `dot.github` so they don't take effect inside this workspace.
2. Add `templates/<id>/template.json` with `title`, `category`, `description`, `stack`, `produces`, `requires` (CLI tools such as `node`), `keywords` (strong matches) and `hints` (weak matches) for auto-selection, `priority` (lower wins ties), `run` / `build` / `customize` notes, `build_steps` (`{"name", "cmd": [...], "platforms"?, "optional"?}` using `{python}`, `{venv_python}`, `{npm}`, `{node}`), `build_outputs` globs, `build_env`, and `packages_executable`.
3. Run `pytest test_agent_builder.py` from the workspace root.
