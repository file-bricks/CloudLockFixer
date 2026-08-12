@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
set PYTHONIOENCODING=utf-8
python clf_app.py %*
set "RC=%ERRORLEVEL%"
echo CloudLockFixer exited with %RC%. Inspect %%LOCALAPPDATA%%\CloudLockFixer\startup.log.
exit /b %RC%
