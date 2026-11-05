@echo off
setlocal EnableExtensions
REM Detect Python first. Upgrade existing only; install only when missing.
set "SILENT="
if /I "%~1"=="/silent" set "SILENT=1"
if /I "%~1"=="--silent" set "SILENT=1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\ensure_python.ps1"
set "RESULT=%ERRORLEVEL%"
if not defined SILENT (
    if "%RESULT%"=="0" (echo Python-kontrollen ar klar.) else (echo Python-kontrollen misslyckades. Ingen extra Python installeras som reserv.)
    pause
)
exit /b %RESULT%
