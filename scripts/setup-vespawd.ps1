# One-time Vespawd setup (installs the Vedaws runtime).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrameworkRoot = Split-Path -Parent $ScriptDir
$PyScript = Join-Path $ScriptDir "setup.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "setup.py not found at $PyScript"
}

Push-Location $FrameworkRoot
try {
    python $PyScript @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
