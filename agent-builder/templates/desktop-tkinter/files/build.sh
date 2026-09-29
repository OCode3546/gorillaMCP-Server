#!/usr/bin/env bash
# Build __APP_TITLE__ for this OS into dist/ (macOS: .app bundle, Linux: single binary).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/python -m unittest discover -s tests -t .
if [[ "$(uname)" == "Darwin" ]]; then
  .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --name __APP_NAME__ app.py
else
  .venv/bin/python -m PyInstaller --noconfirm --clean --onefile --windowed --name __APP_NAME__ app.py
fi
echo "Built: $(ls dist)"
