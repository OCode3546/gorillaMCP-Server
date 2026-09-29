@echo off
REM Build __APP_TITLE__ into dist\__APP_NAME__.exe (run on Windows).
python -m venv .venv || exit /b 1
.venv\Scripts\python -m pip install -r requirements.txt pyinstaller || exit /b 1
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --name __APP_NAME__ main.py || exit /b 1
echo Built dist\__APP_NAME__.exe
