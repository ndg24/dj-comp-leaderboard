@echo off
rem Runs the sync. Used both by the daily Task Scheduler entry and for manual
rem runs. Does NOT pause at the end - a scheduled run must be able to finish
rem and exit unattended. For a manual run, open a terminal and run this file
rem (or `py sync.py` directly) rather than double-clicking, so the output
rem window doesn't close on you before you can read it.

cd /d "%~dp0"
if not exist data mkdir data

echo. >> data\run.log
echo ==== %date% %time% ==== >> data\run.log
powershell -NoProfile -Command "& { .\.venv\Scripts\python.exe sync.py 2>&1 | Tee-Object -FilePath data\run.log -Append }"
exit /b %errorlevel%
