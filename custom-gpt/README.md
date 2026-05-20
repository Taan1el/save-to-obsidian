# Bonus: live-save from a custom GPT

The main script does **batch** imports from a ChatGPT export. If you'd rather save chats *as you go* — straight from a conversation — you can build a custom GPT that writes notes into a GitHub repo your Obsidian vault syncs from (e.g. via the [Obsidian Git](https://github.com/Vinzent03/obsidian-git) plugin).

```
You chat with your GPT  →  it calls a "Save to Obsidian" action
   →  commits a .md file to your vault's GitHub repo (ChatGPT/ folder)
   →  Obsidian Git pulls it into your vault
```

**Heads up on the limits:** a custom GPT only sees chats that happen *inside that GPT* — not your regular ChatGPT history. And it saves when asked, not silently in the background. For your full history, use the main script instead.

## What's in here

- `instructions.md` — paste into your GPT's **Instructions** box.
- `action-schema.json` — paste into the GPT's **Action** schema box. Replace `YOUR_GITHUB_USERNAME/YOUR_REPO` with your own repo.

## Setup (about 5 minutes)

1. **Make an access token.** GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**. Scope it to *only* the repo your vault lives in, with **Contents: Read and write**. Copy the token.
2. **Edit the schema.** In `action-schema.json`, change the `servers` URL to point at your repo:
   `https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_REPO/contents/ChatGPT`
3. **Build the GPT.** In ChatGPT → *Create a GPT* → **Configure** tab:
   - Paste `instructions.md` into Instructions.
   - Tick **Code Interpreter & Data Analysis** (this makes the base64 encoding reliable).
   - **Create new action** → paste the edited schema. Set **Authentication → API Key → Bearer**, and paste your token.
4. **Test.** Ask it: *"Save a test note that says hello."* The `ChatGPT/` folder is created on the first save.

## Why Code Interpreter?

GitHub's API needs file content as base64. Models are bad at doing base64 in their head, so the instructions tell the GPT to run a tiny bit of Python to encode it exactly. That's why the capability needs to be on.
