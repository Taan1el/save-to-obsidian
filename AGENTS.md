# AGENTS.md

## Purpose

Save to Obsidian is a Chrome/Brave extension plus local FastAPI helper that saves visible ChatGPT conversations into an Obsidian vault.

## Stack

- Browser extension: plain HTML/CSS/JavaScript in `extension/`.
- Helper API: Python/FastAPI in `helper/`.
- Tests: Python tests in `tests/`.
- Packaging/validation scripts: PowerShell in `scripts/`.

## Common Commands

```powershell
.\.venv\Scripts\python.exe -m compileall -q helper tests
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-extension.ps1
```

## Rules

- Do not commit `.env`, vault paths, helper tokens, API keys, or packaged zips unless explicitly requested.
- Keep browser extension code dependency-free unless the build/packaging flow changes.
- Keep provider API keys in the helper/local config, not in browser extension storage.
- Preserve localhost helper behavior on `127.0.0.1`; do not add remote upload paths without explicit review.

## Automation Checks

- Compile `helper` and `tests`.
- Run the standard-library unittest suite.
- Check manifest paths, popup/options scripts, and helper CORS/token handling.
