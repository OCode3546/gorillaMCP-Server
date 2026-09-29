# Agent: Builder Agent (code generator)

Code generator that scaffolds complete, runnable projects (web apps, APIs, desktop apps and executables, games, CLIs) from templates and can build them.

Entrypoint:

- `run_agent.py` exposes `run(task: dict) -> dict` and a CLI (`--task-json`, `--task-file`, `--list-templates`).

Modes (`task["mode"]`):

- `plan` (default): dry run. Picks a template from the goal and lists the files it would write.
- `generate` (alias `apply`): writes the project. Existing files are kept unless `overwrite` is true, and nothing is deleted.
- `build`: installs dependencies and runs the template's build steps (tests, Vite, PyInstaller, electron-builder) for a generated project.
- `templates`: lists the available templates.

Task fields: `goal`, `template`, `name`, `title`, `description`, `destination` (exact project folder), `targets[0]` (parent folder; default `agent-builder/generated/`), `overwrite`, `build` (build right after generate), `project` (folder for `build` mode), `env` (extra build environment variables).

Templates live in `templates/<id>/` (`template.json` + `files/`); see README.md for how to add one.
