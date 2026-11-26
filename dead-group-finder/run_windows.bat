@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run install_windows.bat first.& pause& exit /b 1)
if not exist ".env" (echo Copy .env.example to .env and edit it.& pause& exit /b 1)
set PYTHONPATH=%CD%\src
.venv\Scripts\python.exe -m deadgroupfinder.main
pause
