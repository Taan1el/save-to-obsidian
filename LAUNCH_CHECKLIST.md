# Launch Checklist

## Required Gates

- Helper tests pass: `python -B -m unittest discover -s tests -p "test_*.py"`.
- Extension JS parses: `node --check extension\content.js`, `popup.js`, `options.js`, `background.js`.
- Manifest is valid MV3 JSON.
- Icons exist at 16, 32, 48, and 128 px.
- Secret scan finds no API keys or helper tokens outside ignored `.env`.
- Headless Chrome content extraction and popup screenshot smoke pass.
- Local helper returns `/health` on the configured port.
- Full save writes Markdown inside `OBSIDIAN_VAULT_PATH\OBSIDIAN_CHATGPT_FOLDER`.
- Summary and main idea work with Ollama when `AI_PROVIDER=ollama` and `OLLAMA_MODEL` is pulled.
- Extension is reloaded in Chrome after file changes.
- Options page helper URL matches `HELPER_PORT`.
- `PRIVACY.md`, `SECURITY.md`, and `STORE_LISTING.md` are present and match actual behavior.
- Extension package contains only extension runtime files and no `.env`, helper code, pycache, source maps, or generated `dist` files.

## Release Commands

```powershell
cd "C:\Users\YOUR_NAME\Documents\save-to-obsidian"
.\scripts\validate.ps1
.\scripts\package-extension.ps1
```

## Current Proof Snapshot

Verified on 2026-05-22:

- `package-extension.ps1` passed all validation gates and produced `dist\chatgpt-obsidian-saver-extension.zip`.
- Helper health returned `{ "ok": true }` on `http://127.0.0.1:8766`.
- Unauthorized `/save` returned `401`.
- `/docs` returned `404` with `HELPER_DEV=0`.
- Tokened `/diagnostics` reported bind `127.0.0.1` and provider `ollama`.
- Live `full`, `summary`, and `main-idea` saves wrote Markdown notes into the configured Obsidian folder.
- The packaged zip contains only extension runtime files: manifest, background/content scripts, popup/options assets, and four icon PNGs.
- `PRIVACY.md`, `SECURITY.md`, and `STORE_LISTING.md` were added for public release disclosures and permission justification.
- Secret scan covers OpenAI, Anthropic, Gemini/Google, Groq-style, OpenAI-compatible, and helper-token patterns outside ignored `.env`.
- Headless Chrome extraction smoke and fresh popup screenshot smoke passed.
- Known machine caveat: another process still listens on `127.0.0.1:8765`; this project now uses `8766`.
- Public release caveat: choose a license and host the privacy policy before publishing source or submitting to the Chrome Web Store.

## Manual Browser Smoke Test

1. Open `chrome://extensions`.
2. Reload `ChatGPT Obsidian Saver`.
3. Open extension options.
4. Confirm helper URL is `http://127.0.0.1:8766` on this machine.
5. Open a ChatGPT conversation.
6. Run `Save full`, `Save summary`, and `Save main idea`.
7. Confirm each note appears under your configured `OBSIDIAN_VAULT_PATH\OBSIDIAN_CHATGPT_FOLDER`.
