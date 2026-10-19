@echo off
setlocal
cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
  start "UGOT Sketch Studio" pythonw tools\sketch_studio.py
) else (
  python tools\sketch_studio.py
)
