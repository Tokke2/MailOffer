@echo off
setlocal EnableExtensions
REM ===========================================================================
REM Installera_Python.bat - enda .bat-filen i projektet.
REM Installerar senaste Python 3.12 fran python.org (eller winget),
REM anvandarinstallation + PATH, helt tyst (/quiet).
REM
REM   Installera_Python.bat           Manuell korning: status + paus i slutet.
REM   Installera_Python.bat /silent   Tyst lage utan paus - anvands av
REM                                   Starta EmailApp.vbs vid appstart.
REM
REM Finns Python 3.12+ redan avslutar filen DIREKT (snabb startkontroll),
REM sa den ar saker att kora i varje startkedja.
REM OBS: bara ASCII i filen (inga svenska tecken) - inga kodtabellproblem.
REM ===========================================================================

set "SILENT="
if /I "%~1"=="/silent" set "SILENT=1"
if /I "%~1"=="--silent" set "SILENT=1"

REM --- Redan OK? Python 3.12+ via py-launcher, PATH eller standardmapp -----
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 goto :AlreadyOk
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 goto :AlreadyOk
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" goto :AlreadyOk

if not defined SILENT (
    echo.
    echo  E-postofferten - installerar Python 3.12
    echo  =========================================
    echo.
)

REM --- 1) winget (enklast nar det finns) ------------------------------------
where winget >nul 2>&1
if errorlevel 1 goto :PythonOrg
winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity --scope user
if not errorlevel 1 goto :Done

REM --- 2) python.org: senaste 3.12.x-installeraren ---------------------------
:PythonOrg
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$ver=$null;" ^
  "try { $html=(Invoke-WebRequest -UseBasicParsing 'https://www.python.org/downloads/windows/').Content;" ^
  "  $m=[regex]::Matches($html,'python-(3\.12\.\d+)-amd64\.exe');" ^
  "  if ($m.Count -gt 0) { $ver=$m[0].Groups[1].Value } } catch {}" ^
  "if (-not $ver) { $ver='3.12.10' }" ^
  "$url='https://www.python.org/ftp/python/'+$ver+'/python-'+$ver+'-amd64.exe';" ^
  "$out=Join-Path $env:TEMP ('python-'+$ver+'-amd64.exe');" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out;" ^
  "Start-Process -FilePath $out -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 SimpleInstall=1' -Wait;"
goto :Done

:AlreadyOk
if not defined SILENT echo Python 3.12+ finns redan - inget att installera.
exit /b 0

:Done
if not defined SILENT (
    echo.
    echo Klart. Starta E-postofferten med "Starta EmailApp.vbs"
    echo (eller dubbelklicka pa main.pyw).
    echo.
    pause
)
exit /b 0
