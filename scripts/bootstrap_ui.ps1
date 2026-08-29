param(
    [int]$HttpPort = 7860,
    [int]$WsPort = 8765,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

function Test-RstmServer {
    param([int]$Port)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content -match "<title>"
    } catch {
        return $false
    }
}

function Find-CompatiblePython {
    $candidates = @(
        @{ Executable = "py"; Prefix = @("-3") },
        @{ Executable = "python"; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            $versionArguments = @($candidate.Prefix) + @(
                "-c",
                "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))"
            )
            $version = & $candidate.Executable $versionArguments 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $parts = $version.Trim().Split(".")
            if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10 -and [int]$parts[1] -le 14) {
                return $candidate
            }
        } catch {
            continue
        }
    }
    return $null
}

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$venvHealthy = $false
if (Test-Path -LiteralPath $venvPython) {
    try {
        & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        $venvHealthy = $LASTEXITCODE -eq 0
    } catch {
        $venvHealthy = $false
    }
}

if (-not $venvHealthy) {
    $python = Find-CompatiblePython
    if (-not $python) {
        Write-Host "Python 3.10-3.14 was not found." -ForegroundColor Red
        Write-Host "Install 64-bit Python from https://www.python.org/downloads/windows/ and run start_ui.cmd again."
        exit 2
    }
    Write-Host "Creating a local Python environment..."
    # Equivalent command: -m venv --clear .venv
    $venvArguments = @($python.Prefix) + @("-m", "venv", "--clear", ".venv")
    & $python.Executable $venvArguments
    if ($LASTEXITCODE -ne 0) { throw "Unable to create the local Python environment." }
}

$requirementsPath = Join-Path $ProjectRoot "requirements-runtime.txt"
$requirementsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $requirementsPath).Hash
$markerPath = Join-Path $ProjectRoot ".venv\.rstm-runtime.sha256"
$installedHash = if (Test-Path -LiteralPath $markerPath) { (Get-Content -LiteralPath $markerPath -Raw).Trim() } else { "" }
if ($installedHash -ne $requirementsHash) {
    Write-Host "Installing the runtime dependencies. Internet access may be required on first launch..."
    & $venvPython -m pip install --disable-pip-version-check -r $requirementsPath
    if ($LASTEXITCODE -ne 0) { throw "Runtime dependency installation failed." }
    [System.IO.File]::WriteAllText($markerPath, $requirementsHash, [System.Text.Encoding]::ASCII)
}

if ($SetupOnly) {
    return
}

if (Test-RstmServer -Port $HttpPort) {
    Start-Process "http://127.0.0.1:$HttpPort/"
    return
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".env"))) {
    Write-Warning "The .env credential file is missing. The interface will open, but Doubao voice and CPAS services cannot start until it is configured."
}

Start-Job -ScriptBlock {
    param($Url)
    Start-Sleep -Seconds 2
    Start-Process $Url
} -ArgumentList "http://127.0.0.1:$HttpPort/" | Out-Null

$env:PYTHONUTF8 = "1"
& $venvPython (Join-Path $ProjectRoot "ui_server.py") --http-port $HttpPort --ws-port $WsPort
exit $LASTEXITCODE