$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& .\scripts\validate.ps1

$Dist = Join-Path $ProjectRoot "dist"
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
$Zip = Join-Path $Dist "save-to-obsidian-extension.zip"
if (Test-Path -LiteralPath $Zip) {
    Remove-Item -LiteralPath $Zip -Force
}

Compress-Archive -Path (Join-Path $ProjectRoot "extension\*") -DestinationPath $Zip -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($Zip)
try {
    $entries = @($archive.Entries | ForEach-Object { $_.FullName -replace "\\", "/" })
} finally {
    $archive.Dispose()
}

$required = @(
    "manifest.json",
    "background.js",
    "content.js",
    "popup.html",
    "popup.css",
    "popup.js",
    "options.html",
    "options.css",
    "options.js",
    "icons/icon-16.png",
    "icons/icon-32.png",
    "icons/icon-48.png",
    "icons/icon-128.png"
)
foreach ($item in $required) {
    if ($entries -notcontains $item) {
        throw "Packaged extension missing $item"
    }
}

$forbidden = $entries | Where-Object {
    $_ -match "(^|/)\.env$" -or
    $_ -match "__pycache__|\.pyc$|\.map$|node_modules|dist/"
}
if ($forbidden) {
    throw "Forbidden file in extension package: $($forbidden -join ', ')"
}

Write-Host "PACKAGED $Zip"
