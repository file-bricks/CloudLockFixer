@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
where pythonw >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)
start "" pythonw -m cloudlockfixer
