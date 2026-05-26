# Security

## Boundary

The browser extension never writes directly to the filesystem. It sends JSON to a helper app that listens on `127.0.0.1`. The helper validates `X-Obsidian-Saver-Token` before diagnostics or save operations.

## Filesystem Safety

The helper ignores file paths from the extension. It resolves the configured vault path and output folder, rejects traversal in `OBSIDIAN_CHATGPT_FOLDER`, sanitizes note filenames, and verifies the final output directory stays inside the configured vault.

## Secrets

Store `HELPER_TOKEN` and AI provider keys only in the helper `.env` file or process environment. The extension stores only the helper URL and helper token in Chrome extension storage. Do not put provider API keys in extension files.

## Network

The helper binds to `127.0.0.1` only. CORS accepts local extension origins by default. For a published Chrome Web Store build, set `ALLOWED_EXTENSION_ORIGIN=chrome-extension://<published-extension-id>` after the extension ID is known.

## Reporting

For public release, add a public issue tracker or security contact before publishing. Do not include secrets in bug reports, screenshots, logs, or Markdown notes.
