# Media guide

Use these assets for beta sharing and the first Chrome Web Store draft.

## Generated assets

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-media.ps1
```

This creates:

```text
media\popup.png
media\popup-ready.png
media\popup-saved.png
media\options.png
media\walkthrough.gif
```

`popup-ready.png`, `popup-saved.png`, and `walkthrough.gif` are generated demo assets. They are good enough for a GitHub README. For the Chrome Web Store, take real screenshots from Chrome.

## Screenshots to take for Chrome Web Store

Take these from the loaded extension, not from development mock files:

1. `popup-ready.png`
   - ChatGPT page open.
   - Helper running.
   - Popup says `Helper ready`.
   - Shows the three save buttons.

2. `saved-full.png`
   - Same popup after clicking `Save full`.
   - Green message says `Saved: ...md`.

3. `options.png`
   - Options page showing helper URL field and token field.
   - Blur or hide the token.

4. `obsidian-note.png`
   - Obsidian open to the saved Markdown note.
   - Show YAML frontmatter and one user/assistant section.

5. `summary-mode.png`
   - Popup after `Save summary`, or saved summary note in Obsidian.
   - Use Ollama if you want a no-cloud demo.

## Easy GIF/video workflow on Windows

Best manual tool: ScreenToGif.

1. Open ChatGPT, Obsidian, and the extension popup.
2. Record this flow:
   - start helper
   - open popup
   - click `Save full`
   - switch to Obsidian and show the new note
3. Export as GIF or MP4.
4. Keep it under 20 seconds.

Suggested script:

```text
Start helper. Open ChatGPT. Click Save full. The note appears in Obsidian with frontmatter and clean Markdown.
```

For GitHub, use GIF. For Chrome Web Store, use still screenshots first. Video is optional.
