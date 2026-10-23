' ============================================================================
' Starta EmailApp.vbs - starta E-postofferten UTAN konsolfonster.
'
' Kedja vid dubbelklick och autostart (registret pekar hit via wscript):
'   1. Leta pythonw.exe (Python 3.12 forst, sedan ovriga 3.x-installationer).
'   2. Saknas Python: kor Installera_Python.bat /silent DOLT och vanta
'      tills installationen ar klar, leta sedan igen.
'   3. Starta main.pyw med pythonw (ingen konsol). Argument skickas
'      vidare, t.ex. --background fran autostarten.
'
' All text i filen ar medvetet ASCII (inga svenska tecken) sa att den
' aldrig blir mojibake oavsett Windows-kodtabell.
' ============================================================================
Option Explicit

Dim shell, fso, scriptDir, pythonw, batPath, args, i, exitCode, launchError, launchCode
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

LogStage "Launcher started; folder=" & scriptDir
pythonw = FindPythonw()
If pythonw = "" Then
    batPath = scriptDir & "\Installera_Python.bat"
    If fso.FileExists(batPath) Then
        ' 0 = dolt fonster, True = vanta tills klart
        LogStage "Installer starting"
        On Error Resume Next
        exitCode = shell.Run("cmd /c """ & batPath & """ /silent", 0, True)
        launchCode = Err.Number
        launchError = Err.Description
        On Error GoTo 0
        LogStage "Installer ended; exit code=" & exitCode & "; script error=" & launchCode & " " & launchError
        pythonw = FindPythonw()
    End If
End If

args = ""
For i = 0 To WScript.Arguments.Count - 1
    args = args & " """ & WScript.Arguments(i) & """"
Next

shell.CurrentDirectory = scriptDir
If pythonw <> "" Then
    LogStage "Interpreter=" & pythonw
    On Error Resume Next
    exitCode = shell.Run("""" & pythonw & """ """ & scriptDir & "\main.pyw""" & args, 1, True)
    launchError = Err.Description
    If Err.Number <> 0 Then
        LogStage "Launch error=" & launchError
        MsgBox "Kunde inte starta appen: " & launchError & vbCrLf & "Se logs\launcher.log", vbExclamation, "E-postofferten"
    Else
        LogStage "Process ended; exit code=" & exitCode
        If exitCode <> 0 Then MsgBox "Appen avslutades med felkod " & exitCode & vbCrLf & "Se logs\diagnostics.log och logs\launcher.log", vbExclamation, "E-postofferten"
    End If
    On Error GoTo 0
Else
    ' Sista utvag: Python Launcher (pyw.exe) om den finns i PATH.
    On Error Resume Next
    LogStage "Fallback interpreter=pyw.exe -3.12"
    exitCode = shell.Run("pyw.exe -3.12 """ & scriptDir & "\main.pyw""" & args, 1, True)
    launchCode = Err.Number
    launchError = Err.Description
    LogStage "Fallback process ended; exit code=" & exitCode & "; error=" & launchCode & " " & launchError
    If launchCode <> 0 Then
        MsgBox "Python 3.12 kunde inte hittas eller installeras." & vbCrLf & _
               "Kor Installera_Python.bat manuellt och forsok igen.", _
               vbExclamation, "E-postofferten"
    End If
    On Error GoTo 0
End If

Function FindPythonw()
    Dim localAppData, candidates, j, candidate
    FindPythonw = ""
    localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    candidates = Array( _
        scriptDir & "\.venv\Scripts\pythonw.exe", _
        scriptDir & "\venv\Scripts\pythonw.exe", _
        scriptDir & "\python\pythonw.exe", _
        localAppData & "\Programs\Python\Python312\pythonw.exe", _
        localAppData & "\Programs\Python\Python313\pythonw.exe", _
        localAppData & "\Programs\Python\Python314\pythonw.exe", _
        localAppData & "\Programs\Python\Python311\pythonw.exe", _
        localAppData & "\Programs\Python\Python310\pythonw.exe", _
        "C:\Program Files\Python312\pythonw.exe", _
        "C:\Program Files\Python313\pythonw.exe")
    For j = 0 To UBound(candidates)
        candidate = candidates(j)
        LogStage "Probe interpreter=" & candidate
        If fso.FileExists(candidate) Then
            FindPythonw = candidate
            Exit Function
        End If
    Next
End Function


Sub LogStage(message)
    Dim folder, path, stream
    On Error Resume Next
    folder = scriptDir & "\logs"
    If Not fso.FolderExists(folder) Then fso.CreateFolder folder
    path = folder & "\launcher.log"
    If fso.FileExists(path) Then
        If fso.GetFile(path).Size > 1048576 Then
            If fso.FileExists(path & ".1") Then fso.DeleteFile path & ".1", True
            fso.MoveFile path, path & ".1"
        End If
    End If
    Set stream = fso.OpenTextFile(path, 8, True, -1)
    If Err.Number <> 0 Then
        Err.Clear
        path = shell.ExpandEnvironmentStrings("%TEMP%") & "\MailOffer-launcher.log"
        Set stream = fso.OpenTextFile(path, 8, True, -1)
    End If
    stream.WriteLine CStr(Now) & " | " & message
    stream.Close
    On Error GoTo 0
End Sub
