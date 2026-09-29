#!/usr/bin/env bash
# Build __APP_TITLE__ for this OS into dist/ (macOS: .app bundle, Linux: single binary).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pyinstaller
if [[ "$(uname)" == "Darwin" ]]; then
  .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --name __APP_NAME__ main.py
else
  .venv/bin/python -m PyInstaller --noconfirm --clean --onefile --windowed --name __APP_NAME__ main.py
fi
echo "Built: $(ls dist)"
