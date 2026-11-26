@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
 echo Python 3.11+ not found. Install from https://www.python.org/downloads/windows/
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto :error
if not exist ".env" copy .env.example .env >nul
echo Install complete. Edit .env, then run run_windows.bat.
pause
exit /b 0
:error
echo Installation failed.
pause
exit /b 1
