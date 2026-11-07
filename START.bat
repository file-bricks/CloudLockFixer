@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "%~dp0dist\CloudLockFixer\CloudLockFixer.exe" (
    start "" "%~dp0dist\CloudLockFixer\CloudLockFixer.exe" %*
    exit /b 0
)

if exist "%~dp0dist\CloudLockFixer.exe" (
    start "" "%~dp0dist\CloudLockFixer.exe" %*
    exit /b 0
)

if exist "C:\_Local_DEV\CloudLockFixer\CloudLockFixer.exe" (
    start "" "C:\_Local_DEV\CloudLockFixer\CloudLockFixer.exe" %*
    exit /b 0
)

set "PYTHONPATH=%~dp0src"
where pythonw >nul 2>&1
if not errorlevel 1 (
    start "" pythonw -m cloudlockfixer %*
    exit /b 0
)

where python >nul 2>&1
if not errorlevel 1 (
    python -m cloudlockfixer %*
    exit /b %ERRORLEVEL%
)

echo [FEHLER] Weder CloudLockFixer.exe noch Python gefunden!
pause
exit /b 1
