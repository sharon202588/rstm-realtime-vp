param(
    [string]$ReleaseRoot = "",
    [string]$Version = "",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if ([string]::IsNullOrWhiteSpace($ReleaseRoot)) {
    $ReleaseRoot = Join-Path (Split-Path -Parent $ProjectRoot) "RealtimeVoiceVP"
}
$ReleaseRoot = [IO.Path]::GetFullPath($ReleaseRoot)
. (Join-Path $PSScriptRoot "release_version.ps1")

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = Get-NextReleaseVersion -ReleaseRoot $ReleaseRoot
} elseif ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must use major.minor.patch format, for example 1.0.0."
}

$releaseName = "RealtimeVoiceVP V$Version"
$releasePath = Join-Path $ReleaseRoot $releaseName
if (Test-Path -LiteralPath $releasePath) {
    throw "Release already exists and will not be overwritten: $releasePath"
}

& (Join-Path $PSScriptRoot "bootstrap_ui.ps1") -SetupOnly
if ($LASTEXITCODE -ne 0) { throw "The source runtime could not be prepared." }

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
& $python -m pip install --disable-pip-version-check -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller could not be installed." }

$buildToken = [Guid]::NewGuid().ToString("N")
$distPath = Join-Path $ProjectRoot ".tmp\release-dist\$buildToken"
$workPath = Join-Path $ProjectRoot ".tmp\pyinstaller\$buildToken"
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name "RealtimeVoiceVP" `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $workPath `
    --add-data "$ProjectRoot\ui\static;ui\static" `
    --add-data "$ProjectRoot\specs;specs" `
    (Join-Path $ProjectRoot "ui_server.py")
if ($LASTEXITCODE -ne 0) { throw "The portable executable build failed." }

$stagingApp = Join-Path $distPath "RealtimeVoiceVP"
Copy-Item -LiteralPath (Join-Path $ProjectRoot "packaging\start_portable.cmd") -Destination (Join-Path $stagingApp "start_ui.cmd") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "packaging\README_PORTABLE.txt") -Destination (Join-Path $stagingApp "README_PORTABLE.txt") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "env.example") -Destination (Join-Path $stagingApp "env.example") -Force
[IO.File]::WriteAllText((Join-Path $stagingApp "VERSION.txt"), $Version, [Text.Encoding]::ASCII)

$envPath = Join-Path $ProjectRoot ".env"
if (Test-Path -LiteralPath $envPath) {
    Copy-Item -LiteralPath $envPath -Destination (Join-Path $stagingApp ".env") -Force
} else {
    Write-Warning "No .env file was found. Configure credentials in the release folder before voice testing."
}

$dataPath = Join-Path $ProjectRoot "data"
if (Test-Path -LiteralPath $dataPath) {
    Copy-Item -LiteralPath $dataPath -Destination $stagingApp -Recurse -Force
}

New-Item -ItemType Directory -Path $ReleaseRoot -Force | Out-Null
if (Test-Path -LiteralPath $releasePath) {
    throw "Release appeared during the build and will not be overwritten: $releasePath"
}
Copy-Item -LiteralPath $stagingApp -Destination $releasePath -Recurse
[IO.File]::WriteAllText((Join-Path $ReleaseRoot "LATEST.txt"), $releaseName, [Text.Encoding]::UTF8)

Write-Host ""
Write-Host "Release ready: $releaseName" -ForegroundColor Green
Write-Host $releasePath
Write-Warning "The release .env file contains private API credentials. Use only on a trusted computer."
if (-not $NoOpen) {
    Start-Process explorer.exe -ArgumentList $ReleaseRoot
}