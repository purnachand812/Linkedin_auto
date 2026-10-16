Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\purna\Desktop\New folder (2)"
WshShell.Run "pythonw.exe dashboard/server.py", 0, False
WshShell.Run "pythonw.exe linkedin/tools/daemon.py", 0, False
