# Create a new Vespawd project (interactive by default).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrameworkRoot = Split-Path -Parent $ScriptDir
$PyScript = Join-Path $ScriptDir "new_project.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "new_project.py not found at $PyScript"
}

Push-Location $FrameworkRoot
try {
    python $PyScript @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
