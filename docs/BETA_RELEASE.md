# Beta release checklist

Use this for the first public beta.

## Ship beta now

Include:

- `README.md`
- `LICENSE`
- `PRIVACY.md`
- `SECURITY.md`
- `STORE_LISTING.md`
- `docs/`
- `extension/`
- `helper/`
- `scripts/`
- `samples/`
- `tests/`
- `start-helper.bat`

Do not include:

- `.env`
- `.venv`
- `__pycache__`
- helper logs
- local Obsidian notes

## Before sharing

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-extension.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-media.ps1
```

Share:

```text
dist\save-to-obsidian-extension.zip
README.md
```

For GitHub, push the source repo and point testers at the README.

## Tester instructions

Tell testers:

1. Install Python 3.11+.
2. Run `scripts\setup-helper.ps1`.
3. Start `start-helper.bat`.
4. Load `extension/` as an unpacked extension.
5. Paste helper URL and token into extension options.
6. Try `Save full` first.

## Wait for Chrome Web Store

Do these after beta feedback:

- Record real screenshots from Chrome and Obsidian.
- Host privacy policy through GitHub Pages.
- Test on clean Windows user and clean Chrome profile.
- Decide final extension name.
- Submit the packaged zip.
- After Chrome assigns an extension ID, document `ALLOWED_EXTENSION_ORIGIN=chrome-extension://<id>`.
