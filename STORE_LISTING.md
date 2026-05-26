# Chrome Web Store Listing Draft

## Single Purpose

Save the visible ChatGPT conversation selected by the user into a local Obsidian vault through a localhost helper app.

## Short Description

Save visible ChatGPT conversations to local Obsidian Markdown notes through a secure localhost helper.

## Detailed Description

Save to Obsidian adds a small popup on ChatGPT pages with three actions: save the visible conversation, save a summary, or save the main idea. The extension sends the selected conversation content to a helper app running on your own computer. The helper writes clean Markdown notes with YAML frontmatter into your configured Obsidian vault folder.

The extension does not write to the filesystem, does not include a GitHub token, and does not include AI provider API keys. Full saves work without AI. Summary and main idea modes use the provider configured in the local helper.

## Permission Justification

- `activeTab`: access the currently open ChatGPT tab when the user clicks a save action.
- `scripting`: inject the extraction script into already-open ChatGPT tabs after installation or reload.
- `storage`: store the local helper URL and helper token.
- `https://chatgpt.com/*` and `https://chat.openai.com/*`: read visible ChatGPT conversation content.
- `http://127.0.0.1/*` and `http://localhost/*`: communicate with the local helper app.

## Privacy Practices

Data handled: website content from ChatGPT pages, user-provided content inside the selected conversation, extension settings, and the local helper token.

Data use: save selected ChatGPT content into the user's local Obsidian vault. Summary and main idea modes can send selected conversation text to the AI provider configured by the user in the helper.

Data not used for: advertising, analytics, sale, profiling, or unrelated purposes.

## Remote Code

The extension does not execute remote code. AI provider calls happen in the local helper through documented APIs and are used only to generate summary or main idea Markdown when the user chooses those modes.

## Pre-Publish Checklist

- Host `PRIVACY.md` at a public URL and use that URL in the Chrome Web Store dashboard.
- Set Chrome Web Store privacy disclosures to match `PRIVACY.md`.
- After publication assigns a stable extension ID, set helper `ALLOWED_EXTENSION_ORIGIN=chrome-extension://<published-extension-id>` in public setup docs.
- Create final screenshots from the packaged extension, not a development mock.
