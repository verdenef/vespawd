@echo off
REM Double-click to open the friendly Vespawd console (menu).
setlocal
set "SCRIPT=%~dp0scripts\vespawd_console.py"
if not exist "%SCRIPT%" (
    echo ERROR: cannot find scripts\vespawd_console.py next to this file.
    pause
    exit /b 1
)
where py >nul 2>nul
if %ERRORLEVEL%==0 (py -3 "%SCRIPT%" "%~dp0.") else (python "%SCRIPT%" "%~dp0.")
exit /b %ERRORLEVEL%
