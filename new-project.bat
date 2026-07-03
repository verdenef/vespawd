@echo off
REM Double-click to create a new Vespawd project (interactive setup).
setlocal

set "SCRIPT=%~dp0scripts\new_project.py"

if not exist "%SCRIPT%" (
    echo ERROR: cannot find scripts\new_project.py next to this file.
    echo Make sure new-project.bat stays in the Vespawd framework root.
    pause
    exit /b 1
)

REM Prefer the Python launcher, fall back to python on PATH.
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%SCRIPT%" %*
) else (
    python "%SCRIPT%" %*
)

set "RC=%ERRORLEVEL%"

echo.
echo Press any key to close...
pause >nul
exit /b %RC%
