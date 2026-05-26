$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$EnvPath = Join-Path $ProjectRoot ".env"
if (Test-Path -LiteralPath $EnvPath) {
    Get-Content -LiteralPath $EnvPath | ForEach-Object {
        if ($_ -match "^(?<key>[A-Za-z_][A-Za-z0-9_]*)=(?<value>.*)$") {
            [Environment]::SetEnvironmentVariable($Matches.key, $Matches.value, "Process")
        }
    }
}

$Port = if ($env:HELPER_PORT) { $env:HELPER_PORT } else { "8766" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

& $Python -m uvicorn helper.app:app --host 127.0.0.1 --port $Port
