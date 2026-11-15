
$ErrorActionPreference = "Stop"

$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectPath ".venv\Scripts\pythonw.exe"
$BotPath = Join-Path $ProjectPath "bot.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python environment not found. Check the .venv folder."
}

if (-not (Test-Path $BotPath)) {
    throw "bot.py not found."
}

$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "CouchControl.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonPath
$Shortcut.Arguments = "`"$BotPath`""
$Shortcut.WorkingDirectory = $ProjectPath
$Shortcut.Description = "CouchControl Telegram bot"
$Shortcut.Save()

Write-Host "CouchControl startup installed successfully!"
