' ============================================================================
' Starta EmailApp.vbs - starta E-postofferten UTAN konsolfonster.
'
' Kedja vid dubbelklick och autostart (registret pekar hit via wscript):
'   1. Leta pythonw.exe (Python 3.12 forst, sedan ovriga 3.x-installationer).
'   2. Saknas Python: kor Installera_Python.bat /silent DOLT och vanta
'      tills installationen ar klar, leta sedan igen.
'   3. Starta main.pyw med pythonw (dolt fonster). Argument skickas
'      vidare, t.ex. --background fran autostarten.
'
' All text i filen ar medvetet ASCII (inga svenska tecken) sa att den
' aldrig blir mojibake oavsett Windows-kodtabell.
' ============================================================================
Option Explicit

Dim shell, fso, scriptDir, pythonw, batPath, args, i
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = FindPythonw()
If pythonw = "" Then
    batPath = scriptDir & "\Installera_Python.bat"
    If fso.FileExists(batPath) Then
        ' 0 = dolt fonster, True = vanta tills klart
        shell.Run "cmd /c """ & batPath & """ /silent", 0, True
        pythonw = FindPythonw()
    End If
End If

args = ""
For i = 0 To WScript.Arguments.Count - 1
    args = args & " """ & WScript.Arguments(i) & """"
Next

shell.CurrentDirectory = scriptDir
If pythonw <> "" Then
    shell.Run """" & pythonw & """ """ & scriptDir & "\main.pyw""" & args, 0, False
Else
    ' Sista utvag: Python Launcher (pyw.exe) om den finns i PATH.
    On Error Resume Next
    shell.Run "pyw.exe -3.12 """ & scriptDir & "\main.pyw""" & args, 0, False
    If Err.Number <> 0 Then
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
        localAppData & "\Programs\Python\Python312\pythonw.exe", _
        localAppData & "\Programs\Python\Python313\pythonw.exe", _
        localAppData & "\Programs\Python\Python311\pythonw.exe", _
        localAppData & "\Programs\Python\Python310\pythonw.exe", _
        "C:\Program Files\Python312\pythonw.exe", _
        "C:\Program Files\Python313\pythonw.exe")
    For j = 0 To UBound(candidates)
        candidate = candidates(j)
        If fso.FileExists(candidate) Then
            FindPythonw = candidate
            Exit Function
        End If
    Next
End Function
