Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
root = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = root
strPathV6 = root & "\AutoReelSachHay_v6.exe"
strPathDistV6 = root & "\dist\AutoReelSachHay\AutoReelSachHay_v6.exe"
strPathV5 = root & "\AutoReelSachHay_v5.exe"
strPathDistV5 = root & "\dist\AutoReelSachHay\AutoReelSachHay_v5.exe"
strPathV4 = root & "\AutoReelSachHay_v4.exe"
strPathDistV4 = root & "\dist\AutoReelSachHay\AutoReelSachHay_v4.exe"
strPathV3 = root & "\AutoReelSachHay_v3.exe"
strPathDistV3 = root & "\dist\AutoReelSachHay\AutoReelSachHay_v3.exe"
strPathNew = root & "\AutoReelSachHay_v2.exe"
strPathRoot = root & "\AutoReelSachHay.exe"
strPathDistNew = root & "\dist\AutoReelSachHay\AutoReelSachHay_v2.exe"
strPathDist = root & "\dist\AutoReelSachHay\AutoReelSachHay.exe"
If FSO.FileExists(strPathV6) Then
    WshShell.Run """" & strPathV6 & """", 1, False
ElseIf FSO.FileExists(strPathDistV6) Then
    WshShell.Run """" & strPathDistV6 & """", 1, False
ElseIf FSO.FileExists(strPathV5) Then
    WshShell.Run """" & strPathV5 & """", 1, False
ElseIf FSO.FileExists(strPathDistV5) Then
    WshShell.Run """" & strPathDistV5 & """", 1, False
ElseIf FSO.FileExists(strPathV4) Then
    WshShell.Run """" & strPathV4 & """", 1, False
ElseIf FSO.FileExists(strPathDistV4) Then
    WshShell.Run """" & strPathDistV4 & """", 1, False
ElseIf FSO.FileExists(strPathV3) Then
    WshShell.Run """" & strPathV3 & """", 1, False
ElseIf FSO.FileExists(strPathDistV3) Then
    WshShell.Run """" & strPathDistV3 & """", 1, False
ElseIf FSO.FileExists(strPathNew) Then
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
