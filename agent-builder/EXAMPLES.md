# Builder Agent: example prompts

Copy-paste goals for `/agent-builder` (or `run_agent_tool` with `agent_name="agent-builder"`). The agent picks the template; name one explicitly with `template` to override.

| Goal | Template picked |
| --- | --- |
| "Build a snake game exe" | `game-pygame` |
| "Tetris in the browser" | `game-html5` |
| "A landing page for my bakery" | `web-static` |
| "React dashboard for sales numbers" | `web-react` |
| "Flask inventory app with a database" | `web-flask` |
| "Python API for orders" | `api-fastapi` |
| "Windows exe that tracks my expenses" | `desktop-tkinter` |
| "Electron app with an installer for a markdown editor" | `desktop-electron` |
| "Command line tool to rename photos by date" | `cli-python` |

## Typical flow

1. **Plan:** `{"goal": "Build a snake game exe"}` shows the template, folder and file list.
2. **Generate:** add `"mode": "generate"` (and optionally `"destination": "~/Projects/snake"`).
3. **Customise:** edit the generated code for the real goal (for the snake game: replace the dodge logic in `main.py` with snake movement and growth).
4. **Build:** `{"mode": "build", "project": "<project folder>"}` runs tests and packages to `dist/` or `release/`.
5. **Windows .exe from a Mac:** push to GitHub and run the included **Build executables** workflow.
