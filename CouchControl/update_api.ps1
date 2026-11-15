$ErrorActionPreference = "Stop"
$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectPath "requirements.txt"

if (-not (Test-Path $PythonPath)) {
    throw "CouchControl Python environment was not found. Run this script from the installed CouchControl folder."
}
if (-not (Test-Path $Requirements)) {
    throw "requirements.txt was not found."
}

Write-Host "Installing CouchControl updates..."
& $PythonPath -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed. Check the message above."
}
Write-Host ""
Write-Host "Update completed. Restart CouchControl."
