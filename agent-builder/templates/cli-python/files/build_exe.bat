@echo off
REM Build __APP_TITLE__ into dist\__APP_NAME__.exe (run on Windows).
python -m venv .venv || exit /b 1
.venv\Scripts\python -m pip install -e . pyinstaller || exit /b 1
.venv\Scripts\python -m unittest discover -s tests -t . || exit /b 1
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --name __APP_NAME__ --paths src run.py || exit /b 1
echo Built dist\__APP_NAME__.exe
