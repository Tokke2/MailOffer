' ============================================================================
' Starta EmailApp.vbs - starta E-postofferten UTAN konsolfonster.
'
' Kedja vid dubbelklick och autostart (registret pekar hit via wscript):
'   1. Kontrollera/uppdatera gemensam Python och tillagg veckovis, mandagar 08:00.
'   2. Kor Installera_Python.bat /silent DOLT och vanta
'      tills installationen ar klar, leta sedan igen.
'   3. Starta main.pyw med pythonw (ingen konsol). Argument skickas
'      vidare, t.ex. --background fran autostarten.
'
' All text i filen ar medvetet ASCII (inga svenska tecken) sa att den
' aldrig blir mojibake oavsett Windows-kodtabell.
' ============================================================================
Option Explicit

Dim shell, fso, scriptDir, pythonw, batPath, args, i, exitCode, launchError, launchCode, logWarningShown
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
logWarningShown = False

LogStage "Launcher started; folder=" & scriptDir
pythonw = ""
batPath = scriptDir & "\Installera_Python.bat"
If Not fso.FileExists(batPath) Then
    MsgBox "Installera_Python.bat saknas.", vbExclamation, "MailOffer"
    WScript.Quit 1
End If
' Local weekly gate: upgrades only when the Monday 08:00 slot is due.
LogStage "Python startup check starting"
On Error Resume Next
exitCode = shell.Run("cmd /c """ & batPath & """ /silent", 0, True)
launchCode = Err.Number
launchError = Err.Description
On Error GoTo 0
LogStage "Python startup check ended; exit code=" & exitCode & "; error=" & launchCode & " " & launchError
If launchCode <> 0 Or exitCode <> 0 Then
    MsgBox "Kunde inte kontrollera/uppdatera Python och tillagg." & vbCrLf & _
           "Se logs\python-startup.log och logs\launcher.log." & vbCrLf & _
           "Ingen separat Python-miljo installeras som reserv.", vbExclamation, "MailOffer"
    WScript.Quit 1
End If
If fso.FileExists(scriptDir & "\logs\python-runtime.txt") Then
    Dim runtimeFile, processEnv
    Set runtimeFile = fso.OpenTextFile(scriptDir & "\logs\python-runtime.txt", 1, False, -1)
    pythonw = Trim(runtimeFile.ReadAll)
    runtimeFile.Close
End If
If pythonw = "" Or Not fso.FileExists(pythonw) Then
    MsgBox "Kunde inte hitta kontrollerad Python. Start avbruten.", vbExclamation, "MailOffer"
    WScript.Quit 1
End If
Set processEnv = shell.Environment("Process")
processEnv("MAILOFFER_STARTUP_READY") = "1"

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
End If


Sub LogStage(message)
    Dim folder, path, stream, reason, stamp, isoStamp
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
        reason = Err.Description
        Err.Clear
        If Not logWarningShown Then
            logWarningShown = True
            MsgBox "Kan inte skriva loggar i " & folder & vbCrLf & reason & vbCrLf & _
                   "Valj en skrivbar appmapp eller kontrollera mappens behorigheter.", vbExclamation, "MailOffer"
        End If
        Exit Sub
    End If
    stamp = Now
    isoStamp = Year(stamp) & "-" & Right("0" & Month(stamp), 2) & "-" & Right("0" & Day(stamp), 2) & _
               " " & Right("0" & Hour(stamp), 2) & ":" & Right("0" & Minute(stamp), 2) & ":" & Right("0" & Second(stamp), 2)
    stream.WriteLine isoStamp & " | " & message
    stream.Close
    On Error GoTo 0
End Sub
