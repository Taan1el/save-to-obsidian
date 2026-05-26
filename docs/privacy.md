# Privacy Policy

ChatGPT Obsidian Saver has one purpose: save the visible ChatGPT conversation you choose into a local Obsidian vault through a helper app running on your own computer.

## Data Handled

The extension can read visible ChatGPT conversation text on `chatgpt.com` and `chat.openai.com` when you use the save buttons. It also stores your local helper URL and helper token in Chrome extension storage.

The local helper receives the conversation text, page URL, selected save mode, suggested title, and helper token. It writes Markdown files only into the configured Obsidian vault folder.

## Data Not Collected

This project has no analytics, ads, trackers, telemetry, remote logging, or developer-operated backend. The browser extension does not collect browsing history outside the declared ChatGPT pages. The extension does not store GitHub tokens or AI provider API keys.

## AI Providers

Full saves do not use AI. Summary and main idea saves can use the AI provider configured in the local helper. If you configure a cloud provider such as OpenAI, Anthropic, Gemini, or an OpenAI-compatible service, the helper sends the selected conversation text to that provider to generate the requested output. Provider API keys remain in the helper environment or `.env` file and are never stored in the extension.

## Data Sharing

Data is transferred from the extension to `127.0.0.1` or `localhost` so the local helper can write the note. Conversation text is shared with third-party AI providers only when you configure a cloud provider and click `Save summary` or `Save main idea`.

## Storage and Deletion

Saved notes are stored in your configured Obsidian vault. Delete notes from your vault to remove saved conversation files. Remove the extension settings from Chrome storage by uninstalling the extension or clearing extension data. Delete the helper `.env` file to remove local helper configuration and provider keys.

## Chrome Web Store Limited Use

Use of data is limited to the single purpose of saving selected ChatGPT conversations to the user's local Obsidian vault. The project does not sell user data, use data for advertising, or use data for unrelated profiling.
