@echo off
rem Runs the live-update watcher: polls the public campaign total every
rem interval and triggers a full sync.py run (scrape + commit + push) when it
rem changes. Used by the one-off Task Scheduler entry for a live event
rem window. Does NOT pause at the end - a scheduled run must be able to
rem finish and exit unattended.

cd /d "%~dp0"
if not exist data mkdir data

echo. >> data\watch.log
echo ==== %date% %time% ==== >> data\watch.log
powershell -NoProfile -Command "& { .\.venv\Scripts\python.exe watch.py --interval 60 --minutes 120 2>&1 | Tee-Object -FilePath data\watch.log -Append }"
exit /b %errorlevel%
