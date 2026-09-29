# __APP_TITLE__

__APP_DESCRIPTION__

## Install and run

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/__APP_NAME__ --help
.venv/bin/__APP_NAME__ hello Ada
.venv/bin/__APP_NAME__ --json scan .
```

## Test

```bash
python3 -m unittest discover -s tests -t .
```

## Build a single-file executable

- **Windows `.exe`:** run `build_exe.bat` on Windows → `dist\__APP_NAME__.exe`
- **macOS / Linux:** `.venv/bin/pip install pyinstaller && .venv/bin/pyinstaller --onefile --name __APP_NAME__ --paths src run.py`
- **All platforms:** run the **Build executables** GitHub workflow

## Code layout

- `src/__PKG_NAME__/cli.py`: argument parsing and output (`build_parser()`, `cmd_*` handlers)
- `src/__PKG_NAME__/core.py`: logic with no I/O formatting, easy to test
- `run.py`: entry script used by PyInstaller
