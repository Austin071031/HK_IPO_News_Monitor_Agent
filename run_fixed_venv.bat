@echo off
cd /d "%~dp0"

echo Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo Running fixed agent script...
    python run_agents_fixed.py
) else (
    echo Virtual environment not found at .venv
    echo Please create with: python -m venv .venv
    echo Then activate and install dependencies
    pause
)