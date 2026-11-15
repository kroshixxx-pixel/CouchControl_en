$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonVersion = '3.13.17'
$PythonInstaller = Join-Path $env:TEMP "CouchControl-Python-$PythonVersion-amd64.exe"
$PythonDir = Join-Path $ProjectPath 'Python313'
$PythonExe = Join-Path $PythonDir 'python.exe'
$PythonwExe = Join-Path $PythonDir 'pythonw.exe'
$VenvDir = Join-Path $ProjectPath '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$VenvPythonw = Join-Path $VenvDir 'Scripts\pythonw.exe'
$Requirements = Join-Path $ProjectPath 'requirements.txt'
$BotFile = Join-Path $ProjectPath 'bot.py'
$WebServerFile = Join-Path $ProjectPath 'web_server.py'
$InstallLog = Join-Path $env:TEMP 'CouchControl-Python-install.log'
$DiagnosticLog = Join-Path $env:TEMP 'CouchControl-install-diagnostic.log'

try { Start-Transcript -Path $DiagnosticLog -Force | Out-Null } catch {}

function Show-PythonInstallLog {
    if (Test-Path -LiteralPath $InstallLog -PathType Leaf) {
        Write-Host 'Last lines from the official Python installation log:'
        Get-Content -LiteralPath $InstallLog -Tail 60 | ForEach-Object { Write-Host $_ }
    }
}

try {
    Write-Host 'CouchControl setup: checking project files...'
    foreach ($requiredFile in @($Requirements, $BotFile, $WebServerFile)) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            throw "Required CouchControl file is missing: $requiredFile"
        }
    }

    if (-not ((Test-Path -LiteralPath $PythonExe -PathType Leaf) -and (Test-Path -LiteralPath $PythonwExe -PathType Leaf))) {
        Write-Host "Preparing private Python $PythonVersion runtime..."
        # This folder belongs to CouchControl; do not touch the user's other Python installs.
        if (Test-Path -LiteralPath $PythonDir) {
            Remove-Item -LiteralPath $PythonDir -Recurse -Force
        }

        Write-Host 'Downloading the official Python installer...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe" -OutFile $PythonInstaller

        if (-not (Test-Path -LiteralPath $PythonInstaller -PathType Leaf)) {
            throw 'Python installer download did not create a file.'
        }
        $download = Get-Item -LiteralPath $PythonInstaller
        Write-Host "Downloaded installer size: $($download.Length) bytes"
        if ($download.Length -lt 10MB) {
            throw "Downloaded Python installer looks incomplete ($($download.Length) bytes)."
        }

        $signature = Get-AuthenticodeSignature -FilePath $PythonInstaller
        if ($signature.Status -ne 'Valid') {
            throw "The downloaded Python installer signature is not valid: $($signature.Status)."
        }

        if (Test-Path -LiteralPath $InstallLog) {
            Remove-Item -LiteralPath $InstallLog -Force
        }

        Write-Host "Installing private Python into: $PythonDir"

        # Use a fresh CPython minor release so an older registered 3.12 bundle cannot
        # redirect this install into its previous location. Capture Burn's real exit code.
        $pythonArguments = '/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_test=0 Include_pip=1 Shortcuts=0 "TargetDir={0}" "DefaultJustForMeTargetDir={0}" /log "{1}"' -f $PythonDir, $InstallLog
        $pythonProcess = Start-Process -FilePath $PythonInstaller -ArgumentList $pythonArguments -Wait -PassThru -WindowStyle Hidden
        $pythonInstallExitCode = $pythonProcess.ExitCode
        Write-Host "Python installer exit code: $pythonInstallExitCode"
        if ($pythonInstallExitCode -ne 0) {
            Show-PythonInstallLog
            throw "The official Python installer failed with exit code $pythonInstallExitCode."
        }

        # Python 3.13's documented per-user default is the fallback if TargetDir was not honored.
        $defaultPythonDir = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313'
        $candidateDirs = @($PythonDir, $defaultPythonDir)
        $foundPythonDir = $null
        foreach ($candidateDir in $candidateDirs) {
            $candidateExe = Join-Path $candidateDir 'python.exe'
            $candidateWExe = Join-Path $candidateDir 'pythonw.exe'
            if ((Test-Path -LiteralPath $candidateExe -PathType Leaf) -and (Test-Path -LiteralPath $candidateWExe -PathType Leaf)) {
                $foundPythonDir = $candidateDir
                break
            }
        }

        if (-not $foundPythonDir) {
            Show-PythonInstallLog
            throw "Python reported success but neither the requested folder nor the standard per-user folder contains python.exe and pythonw.exe. Expected: $PythonDir"
        }

        if ($foundPythonDir -ne $PythonDir) {
            Write-Warning "Python was installed in its standard per-user folder instead: $foundPythonDir"
            $PythonDir = $foundPythonDir
            $PythonExe = Join-Path $PythonDir 'python.exe'
            $PythonwExe = Join-Path $PythonDir 'pythonw.exe'
        }
    }

    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        throw "Private Python executable is missing: $PythonExe"
    }
    if (-not (Test-Path -LiteralPath $PythonwExe -PathType Leaf)) {
        throw "Private Python windowless executable is missing: $PythonwExe"
    }

    Write-Host 'Checking private Python...'
    & $PythonExe --version
    $pythonExitCode = $LASTEXITCODE
    if ($pythonExitCode -ne 0) {
        throw "Private Python could not start. Exit code: $pythonExitCode"
    }

    Write-Host 'Creating the private virtual environment...'
    if (Test-Path -LiteralPath $VenvDir) {
        Remove-Item -LiteralPath $VenvDir -Recurse -Force
    }
    & $PythonExe -m venv $VenvDir
    $venvExitCode = $LASTEXITCODE
    if ($venvExitCode -ne 0 -or -not (Test-Path -LiteralPath $VenvPython -PathType Leaf) -or -not (Test-Path -LiteralPath $VenvPythonw -PathType Leaf)) {
        throw "Could not create the private virtual environment. Exit code: $venvExitCode"
    }

    Write-Host 'Installing CouchControl dependencies...'
    & $VenvPython -m pip install --disable-pip-version-check --retries 3 --timeout 30 -r $Requirements
    $dependenciesExitCode = $LASTEXITCODE
    if ($dependenciesExitCode -ne 0) {
        throw "Could not install requirements.txt. Exit code: $dependenciesExitCode"
    }

    Write-Host 'Checking Python syntax...'
    & $VenvPython -m compileall -q -f $BotFile $WebServerFile
    $syntaxExitCode = $LASTEXITCODE
    if ($syntaxExitCode -ne 0) {
        throw "CouchControl Python syntax check failed. Exit code: $syntaxExitCode"
    }

    Write-Host 'Checking installed libraries and local API module...'
    & $VenvPython -c "import telegram, dotenv, pyautogui, PIL, pyperclip, aiohttp, cv2, numpy, web_server; print('CouchControl dependencies OK')"
    $moduleExitCode = $LASTEXITCODE
    if ($moduleExitCode -ne 0) {
        throw "CouchControl dependency check failed. Exit code: $moduleExitCode"
    }

    Write-Host 'CouchControl installation completed successfully.'
    Write-Host "Diagnostic log: $DiagnosticLog"
    exit 0
}
catch {
    Write-Host ''
    Write-Host 'COUCHCONTROL INSTALLATION FAILED:' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Diagnostic log: $DiagnosticLog" -ForegroundColor Yellow
    if (Test-Path -LiteralPath $InstallLog -PathType Leaf) {
        Write-Host "Python installer log: $InstallLog" -ForegroundColor Yellow
    }
    exit 1
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
}
