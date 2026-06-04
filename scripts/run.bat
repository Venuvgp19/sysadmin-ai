@echo off
REM SysAdmin AI Launcher for Windows

cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: No virtual environment found. Using system Python.
)

REM Set environment variables
set OLLAMA_HOST=http://localhost:11434
set SYSADMIN_MODEL=qwen2.5:7b
set PYTHONPATH=%CD%

echo.
echo  ================================================
echo   SysAdmin AI Agent
echo  ================================================
echo.

python agent\main.py
