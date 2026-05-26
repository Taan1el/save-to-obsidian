param(
    [string]$VaultPath = "$HOME\Documents\Obsidian Vault",
    [string]$ChatFolder = "AI Chats\ChatGPT\Saved"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Setting up ChatGPT Obsidian Saver helper..."

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not on PATH. Install Python 3.11+ first."
}

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -m venv .venv
    } else {
        python -m venv .venv
    }
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\helper\requirements.txt

if (-not (Test-Path -LiteralPath ".\.env")) {
    Copy-Item -LiteralPath ".\.env.example" -Destination ".\.env"
    $token = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
    $envText = Get-Content -Raw -LiteralPath ".\.env"
    $envText = $envText -replace "OBSIDIAN_VAULT_PATH=.*", "OBSIDIAN_VAULT_PATH=$VaultPath"
    $envText = $envText -replace "OBSIDIAN_CHATGPT_FOLDER=.*", "OBSIDIAN_CHATGPT_FOLDER=$ChatFolder"
    $envText = $envText -replace "HELPER_TOKEN=.*", "HELPER_TOKEN=$token"
    Set-Content -LiteralPath ".\.env" -Value $envText -Encoding UTF8
    Write-Host "Created .env with a new helper token."
} else {
    Write-Host ".env already exists; keeping your current settings."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Next: run .\start-helper.bat"
