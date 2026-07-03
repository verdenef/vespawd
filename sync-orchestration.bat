@echo off
REM Run after your IDE executor updates current_task.md (keeps Vedaws in sync).
setlocal

set "SCRIPT=%~dp0scripts\sync_orchestration.py"

if not exist "%SCRIPT%" (
    echo ERROR: cannot find scripts\sync_orchestration.py next to this file.
    pause
    exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%SCRIPT%" %*
) else (
    python "%SCRIPT%" %*
)

set "RC=%ERRORLEVEL%"
echo.
if %RC% NEQ 0 pause
exit /b %RC%
