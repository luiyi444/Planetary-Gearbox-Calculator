@echo off
REM Opens the calculator in its own window.
REM Requirements: Python 3.9+ with Tkinter, both included in the standard
REM python.org installer. No pip, no virtual environment, no internet.
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python was not found in PATH.
    echo Install Python from https://www.python.org/downloads/ and tick
    echo "Add python.exe to PATH" during the installation.
    echo.
    pause
    exit /b 1
)

python -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo.
    echo This Python installation does not include Tkinter.
    echo Reinstall Python from python.org and keep the
    echo "tcl/tk and IDLE" component selected.
    echo.
    pause
    exit /b 1
)

where pythonw >nul 2>nul
if errorlevel 1 (
    python desktop.py
    exit /b %errorlevel%
)

REM pythonw starts the window without a console hanging around behind it.
start "" pythonw desktop.py
exit /b 0
