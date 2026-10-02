@echo off
setlocal
cd /d "%~dp0"
py -3.12 scripts\launch.py %*
set "result=%errorlevel%"
if not "%result%"=="0" (
  echo Launch failed. Python 3.12 and internet access are required for first-time setup.
  pause
)
exit /b %result%
