@echo off
setlocal EnableExtensions
REM ============================================================================
REM Installera senaste Python.bat
REM Enda .bat-filen i projektet. Installerar senaste stabila Python 3
REM pa den har datorn (anvandarinstallation + PATH). Startar INTE appen.
REM ============================================================================
echo.
echo  E-postofferten – installerar senaste stabila Python
echo  =============================================
echo.

where winget >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Provar winget...
    winget install -e --id Python.Python.3 --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity --scope user
    if %ERRORLEVEL%==0 goto :Done
    winget install -e --id Python.Python.3.13 --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity --scope user
    if %ERRORLEVEL%==0 goto :Done
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity --scope user
    if %ERRORLEVEL%==0 goto :Done
)

echo Laddar ner installer fran python.org...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$ver=$null;" ^
  "try { $html=(Invoke-WebRequest -UseBasicParsing 'https://www.python.org/downloads/windows/').Content;" ^
  "  if ($html -match 'python-(\d+\.\d+\.\d+)-amd64.exe') { $ver=$Matches[1] } } catch {}" ^
  "if (-not $ver) { $ver='3.12.8' }" ^
  "$url='https://www.python.org/ftp/python/'+$ver+'/python-'+$ver+'-amd64.exe';" ^
  "$out=Join-Path $env:TEMP ('python-'+$ver+'-amd64.exe');" ^
  "Write-Host ('Laddar ner '+$url);" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out;" ^
  "Start-Process -FilePath $out -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 SimpleInstall=1' -Wait;"

:Done
echo.
echo Klart. Starta E-postofferten genom att dubbelklicka pa main.pyw
echo (eller pythonw main.pyw).
echo.
pause
exit /b 0
