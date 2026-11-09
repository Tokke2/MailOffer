@echo off
setlocal EnableExtensions
REM Compatibility filename: check existing system Python, update add-ons only.
set "SILENT="
if /I "%~1"=="/silent" set "SILENT=1"
if /I "%~1"=="--silent" set "SILENT=1"
if not exist "%~dp0logs" mkdir "%~dp0logs"
if not exist "%~dp0logs" exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\ensure_python.ps1" >> "%~dp0logs\python-startup.log" 2>&1
set "RESULT=%ERRORLEVEL%"
if not defined SILENT (
    if "%RESULT%"=="0" (echo Python-kontrollen ar klar.) else (echo Python-kontrollen misslyckades. Ingen extra Python installeras som reserv.)
    pause
)
exit /b %RESULT%
