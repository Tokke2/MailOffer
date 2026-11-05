' Weekly maintenance only: no GUI launch and no console.
Option Explicit
Dim shell, fso, root, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
result = shell.Run("cmd /c """ & root & "\Installera_Python.bat"" /silent", 0, True)
WScript.Quit result
