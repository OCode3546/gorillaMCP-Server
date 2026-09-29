# __APP_TITLE__

__APP_DESCRIPTION__

A desktop app built with Tkinter (Python standard library) that packages into a standalone executable with PyInstaller.

## Run from source

```bash
python3 app.py
```

No third-party dependencies are needed to run it. Data is saved to a per-user file (shown in the status bar).

## Test

```bash
python3 -m unittest discover -s tests -t .
```

## Build an executable

| Target | How |
| --- | --- |
| Windows `.exe` | Run `build_exe.bat` on Windows → `dist\__APP_NAME__.exe` |
| macOS `.app` / Linux binary | `./build.sh` → `dist/` |
| All three | Push to GitHub and run the **Build executables** workflow (or push a `v*` tag) |

PyInstaller builds for the OS it runs on. It cannot make a Windows `.exe` on macOS or Linux, which is why the GitHub workflow is included.

## Code layout

- `store.py`: data model and JSON persistence, no UI (tested in `tests/`)
- `app.py`: the Tkinter UI; `_build_menu()`, `_build_ui()` and `on_*` event handlers
