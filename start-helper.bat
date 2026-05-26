@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Local Python environment not found.
  echo Run: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-helper.ps1
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File ".\helper\run.ps1"
pause
