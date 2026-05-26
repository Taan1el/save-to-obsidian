$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path -LiteralPath $Chrome)) {
    $Chrome = "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
}
if (-not (Test-Path -LiteralPath $Chrome)) {
    throw "Chrome or Brave executable not found."
}

$MediaDir = Join-Path $ProjectRoot "media"
New-Item -ItemType Directory -Force -Path $MediaDir | Out-Null

function Capture-Page {
    param(
        [string]$Source,
        [string]$Output,
        [string]$Size = "460,520"
    )

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString("N") + ".png")
    $url = ([Uri](Resolve-Path $Source).Path).AbsoluteUri
    Start-Process -FilePath $Chrome -ArgumentList @(
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--window-size=$Size",
        "--screenshot=$tmp",
        $url
    ) -Wait -PassThru -WindowStyle Hidden | Out-Null

    if (-not (Test-Path -LiteralPath $tmp) -or (Get-Item -LiteralPath $tmp).Length -eq 0) {
        throw "Screenshot failed for $Source"
    }

    Copy-Item -LiteralPath $tmp -Destination (Join-Path $MediaDir $Output) -Force
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}

Capture-Page -Source "extension\popup.html" -Output "popup.png" -Size "460,520"
Capture-Page -Source "extension\options.html" -Output "options.png" -Size "860,520"

function Capture-PopupVariant {
    param(
        [string]$Output,
        [string]$HelperText,
        [string]$DotClass,
        [string]$Message,
        [string]$MessageClass = ""
    )

    $source = Get-Content -Raw -LiteralPath "extension\popup.html"
    $source = $source -replace '<script src="popup\.js"></script>', ''
    $script = @"
<script>
document.getElementById("helperText").textContent = "$HelperText";
document.getElementById("statusDot").className = "status-dot $DotClass";
const message = document.getElementById("messageBox");
message.textContent = "$Message";
message.className = "message $MessageClass";
</script>
"@
    $tmpPopup = Join-Path $ProjectRoot "extension\__capture_popup.html"
    Set-Content -LiteralPath $tmpPopup -Value ($source -replace '</body>', "$script`n</body>") -Encoding UTF8
    try {
        Capture-Page -Source "extension\__capture_popup.html" -Output $Output -Size "460,520"
    } finally {
        Remove-Item -LiteralPath $tmpPopup -Force -ErrorAction SilentlyContinue
    }
}

Capture-PopupVariant -Output "popup-ready.png" -HelperText "Helper ready" -DotClass "is-ready" -Message "Ready" -MessageClass ""
Capture-PopupVariant -Output "popup-saved.png" -HelperText "Helper ready" -DotClass "is-ready" -Message "Saved: 2026-05-26-top-cars-for-living.md" -MessageClass "is-success"

@'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

media = Path("media")
frames = []

W, H = 960, 540
bg = (24, 24, 27)
panel = (36, 36, 40)
purple = (126, 96, 255)
green = (68, 208, 113)
text = (245, 245, 245)
muted = (176, 176, 186)

try:
    font_title = ImageFont.truetype("arial.ttf", 44)
    font_h = ImageFont.truetype("arial.ttf", 30)
    font = ImageFont.truetype("arial.ttf", 23)
    font_small = ImageFont.truetype("arial.ttf", 19)
except OSError:
    font_title = font_h = font = font_small = ImageFont.load_default()

def frame(title, lines, accent=purple):
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((54, 54, W - 54, H - 54), radius=18, fill=panel)
    d.rounded_rectangle((54, 54, W - 54, 122), radius=18, fill=accent)
    d.text((86, 70), title, fill=text, font=font_title)
    y = 170
    for line in lines:
        if line.startswith("$ "):
            d.rounded_rectangle((86, y - 8, W - 86, y + 42), radius=8, fill=(18, 18, 20))
            d.text((108, y), line, fill=(214, 214, 220), font=font_small)
            y += 70
        else:
            d.text((98, y), line, fill=text if not line.startswith("-") else muted, font=font)
            y += 44
    return img

frames.append(frame("1. Start the helper", [
    "$ start-helper.bat",
    "- helper listens on 127.0.0.1:8766",
    "- token stays local in .env",
    "- Obsidian folder is configured by you",
]))
frames.append(frame("2. Load extension", [
    "- open chrome://extensions",
    "- enable Developer mode",
    "- Load unpacked -> extension folder",
    "- set helper URL and token in Options",
]))
frames.append(frame("3. Save from ChatGPT", [
    "- open any ChatGPT conversation",
    "- click Obsidian Saver",
    "- Save full works without AI",
    "- summary modes use helper-side provider",
], green))
frames.append(frame("4. Note appears in Obsidian", [
    "AI Chats/ChatGPT/Saved",
    "- clean Markdown",
    "- YAML frontmatter",
    "- original ChatGPT URL",
    "- no manual .md download",
], green))

frames[0].save(
    media / "walkthrough.gif",
    save_all=True,
    append_images=frames[1:],
    duration=1500,
    loop=0,
    optimize=True,
)
print("created media/walkthrough.gif")
'@ | python -

Write-Host "Created media assets in $MediaDir"
