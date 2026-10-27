Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
root = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = root
strPathNew = root & "\AutoReelSachHay_v2.exe"
strPathRoot = root & "\AutoReelSachHay.exe"
strPathDistNew = root & "\dist\AutoReelSachHay\AutoReelSachHay_v2.exe"
strPathDist = root & "\dist\AutoReelSachHay\AutoReelSachHay.exe"
If FSO.FileExists(strPathNew) Then
    WshShell.Run """" & strPathNew & """", 1, False
ElseIf FSO.FileExists(strPathRoot) Then
    WshShell.Run """" & strPathRoot & """", 1, False
ElseIf FSO.FileExists(strPathDistNew) Then
    WshShell.Run """" & strPathDistNew & """", 1, False
ElseIf FSO.FileExists(strPathDist) Then
    WshShell.Run """" & strPathDist & """", 1, False
Else
    WshShell.Run "python -X utf8 app.py", 0, False
End If
