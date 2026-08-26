@echo off
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: El programa terminó con código %errorlevel%
    pause
)