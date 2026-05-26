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

$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("cos-browser-smoke-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

try {
    $ContentJs = ([Uri](Resolve-Path "extension\content.js").Path).AbsoluteUri
    $Fixture = Join-Path $Tmp "extract-fixture.html"
    $FixtureText = @"
<!doctype html>
<html>
<head><title>Launch Ready Chat - ChatGPT</title></head>
<body>
  <article data-message-author-role="user">
    <div class="whitespace-pre-wrap">Can you save this conversation?</div>
  </article>
  <article data-message-author-role="assistant">
    <div class="markdown"><p>Yes. I will save it as Markdown.</p></div>
    <button>Copy</button>
  </article>
  <pre id="result">pending</pre>
  <script>
    window.chrome = { runtime: { onMessage: { addListener() {} } } };
  </script>
  <script src="$ContentJs"></script>
  <script>
    const result = extractConversation();
    document.getElementById('result').textContent = JSON.stringify(result);
  </script>
</body>
</html>
"@
    [System.IO.File]::WriteAllText($Fixture, $FixtureText, [System.Text.UTF8Encoding]::new($false))

    $dom = & $Chrome --headless=new --disable-gpu --allow-file-access-from-files --dump-dom $Fixture 2>$null
    if ($dom -notmatch '"title":"Launch Ready Chat"' -or $dom -notmatch '"role":"user"' -or $dom -notmatch '"role":"assistant"') {
        throw "Content extraction smoke output did not include expected title/user/assistant JSON."
    }
    Write-Host "content extraction smoke ok"

    $Screenshot = Join-Path $ProjectRoot "dist\popup-smoke.png"
    $TempScreenshot = Join-Path $Tmp "popup-smoke.png"
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Screenshot) | Out-Null
    Remove-Item -LiteralPath $Screenshot -Force -ErrorAction SilentlyContinue
    $Popup = ([Uri](Resolve-Path "extension\popup.html").Path).AbsoluteUri
    $process = Start-Process -FilePath $Chrome -ArgumentList @(
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--window-size=380,360",
        "--screenshot=$TempScreenshot",
        $Popup
    ) -Wait -PassThru -WindowStyle Hidden
    if (-not (Test-Path -LiteralPath $TempScreenshot) -or (Get-Item -LiteralPath $TempScreenshot).Length -eq 0) {
        throw "Popup screenshot smoke failed."
    }
    Copy-Item -LiteralPath $TempScreenshot -Destination $Screenshot -Force
    if ($process.ExitCode -ne 0) {
        Write-Host "popup screenshot Chrome exit code $($process.ExitCode), but fresh screenshot exists"
    }
    Write-Host "popup screenshot smoke ok: $Screenshot"
} finally {
    Remove-Item -LiteralPath $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}
