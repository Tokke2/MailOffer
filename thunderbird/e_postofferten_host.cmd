@echo off
cd /d "%~dp0\.."
set "EMAILAPP_PORTABLE=1"
set "PY="
if exist "%CD%\python\python.exe" set "PY=%CD%\python\python.exe"
if not defined PY if exist "%CD%\python.exe" set "PY=%CD%\python.exe"
if not defined PY (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    if not defined PY set "PY=%%I"
  )
)
if not defined PY (
  for /f "delims=" %%I in ('where py.exe 2^>nul') do (
    if not defined PY set "PY=%%I"
  )
)
if not defined PY exit /b 1
"%PY%" -u "%~dp0native_host.py"
