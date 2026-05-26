$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "== Python syntax =="
python -B -m py_compile helper\app.py helper\config.py helper\markdown_writer.py helper\models.py

Write-Host "== Helper tests =="
python -B -m unittest discover -s tests -p "test_*.py"

Write-Host "== Extension JavaScript syntax =="
node --check extension\content.js
node --check extension\popup.js
node --check extension\options.js
node --check extension\background.js

Write-Host "== Manifest JSON =="
node -e "const fs=require('fs'); const m=JSON.parse(fs.readFileSync('extension/manifest.json','utf8')); if(m.manifest_version!==3) throw new Error('manifest_version must be 3'); if(!m.action.default_popup) throw new Error('missing popup'); console.log('manifest ok')"

Write-Host "== Icon assets =="
@'
import struct
from pathlib import Path
expected = (16, 32, 48, 128)
for size in expected:
    path = Path("extension/icons") / f"icon-{size}.png"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (size, size):
        raise SystemExit(f"{path} has size {(width, height)}")
print("icons ok", list(expected))
'@ | python -

Write-Host "== Secret scan =="
$secretPattern = "sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|gsk_[A-Za-z0-9_-]{20,}|OPENAI_API_KEY=sk-[A-Za-z0-9_-]{20,}|ANTHROPIC_API_KEY=sk-ant-[A-Za-z0-9_-]{20,}|GEMINI_API_KEY=AIza[0-9A-Za-z_-]{20,}|GOOGLE_API_KEY=AIza[0-9A-Za-z_-]{20,}|OPENAI_COMPATIBLE_API_KEY=(sk-|sk-ant-|gsk_|AIza)[A-Za-z0-9_-]{20,}|HELPER_TOKEN=[A-Za-z0-9_-]{32,}"
$secretHits = rg -n $secretPattern --glob "!*.env" --glob "!dist/**" --glob "!scripts/validate.ps1" .
if ($LASTEXITCODE -eq 0) {
    Write-Error "Potential secret found outside ignored .env:`n$secretHits"
}
if ($LASTEXITCODE -gt 1) {
    throw "Secret scan failed"
}

Write-Host "== Local helper health if running =="
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8766/health" -TimeoutSec 3 | ConvertTo-Json -Compress
} catch {
    Write-Host "helper not running on 8766; static/test gates still passed"
}

Write-Host "== Stale helper port check =="
$stale8765 = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($stale8765) {
    Write-Host "warning: stale helper/process is still listening on 8765; launch config uses 8766"
}

Write-Host "== Headless browser smoke =="
& .\scripts\browser-smoke.ps1

Write-Host "VALIDATION PASSED"
