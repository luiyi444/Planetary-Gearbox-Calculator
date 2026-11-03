# Opens the calculator in its own window.
# Requirements: Python 3.9+ with Tkinter, both included in the standard
# python.org installer. No pip, no virtual environment, no internet.
#
# Windows never runs a .ps1 on double-click; use run.bat for that.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found in PATH." -ForegroundColor Red
    Write-Host "Install it from https://www.python.org/downloads/ and tick 'Add python.exe to PATH'."
    exit 1
}

python -c "import tkinter" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "This Python installation does not include Tkinter." -ForegroundColor Red
    Write-Host "Reinstall Python from python.org and keep the 'tcl/tk and IDLE' component."
    exit 1
}

$pythonw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($pythonw) {
    Start-Process $pythonw.Source -ArgumentList "desktop.py" -WorkingDirectory $PSScriptRoot
} else {
    python desktop.py
}
