# __APP_TITLE__

__APP_DESCRIPTION__

A pygame (pygame-ce) arcade game that packages into a standalone executable with PyInstaller.

## Play from source

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip ...
.venv/bin/python main.py
```

**Controls:** ← → or A / D to move (or hold the mouse button), P or Esc to pause, Enter / Space / click to start.

## Build an executable

| Target | How |
| --- | --- |
| Windows `.exe` | Run `build_exe.bat` on Windows → `dist\__APP_NAME__.exe` |
| macOS `.app` / Linux binary | `./build.sh` → `dist/` |
| All three | Push to GitHub and run the **Build executables** workflow (or push a `v*` tag); download the artifacts |

PyInstaller builds for the OS it runs on. It cannot make a Windows `.exe` on macOS or Linux, which is why the GitHub workflow is included.

## Code layout

- `settings.py`: window size, speeds, spawn rates, colours
- `main.py`: `Player`, `Hazard`, `Pickup` entities and the `Game` class (`update(dt)`, `draw()`, input handling)
- `python main.py --smoke-test` simulates five seconds of play headlessly (used by CI)
