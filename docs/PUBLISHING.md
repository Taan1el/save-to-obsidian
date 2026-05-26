# Publishing Guide

This document covers the public-facing setup required before submitting the
extension to the Chrome Web Store. It complements `STORE_LISTING.md` and
closes the open items in the "Pre-Publish Checklist" there.

## Privacy Policy Hosting (GitHub Pages)

The Chrome Web Store dashboard requires a public URL for the privacy policy.
This project will publish source on GitHub before store submission, so the
simplest and most durable option is **GitHub Pages serving the repo's
`/docs` folder on the default branch**.

Why GitHub Pages over the alternatives:

- **Raw GitHub URLs** (`raw.githubusercontent.com/...`) render as plain text
  with no styling, can change shape on a rename, and look unprofessional to
  store reviewers. Ruled out.
- **Personal site / blog** introduces a separate moving piece (DNS, CMS,
  hosting bill) that has to outlive the extension. Ruled out for a single
  indie project.
- **Netlify / Cloudflare Pages** would work but adds a second account, a
  second deploy pipeline, and a second place to update when `PRIVACY.md`
  changes. Not worth the overhead when the repo is already on GitHub.
- **GitHub Pages** is free, version-controlled, served over HTTPS on a
  stable `*.github.io` URL, and updates automatically on every push to the
  default branch. The Markdown file is already in the repo, so there is
  nothing extra to maintain.

### One-Time Setup

1. **Push the repo to GitHub** as a public repository. Suggested name:
   `save-to-obsidian`. Confirm `PRIVACY.md` (root) and this
   `docs/PUBLISHING.md` are committed.

2. **Copy `PRIVACY.md` into `docs/`** so GitHub Pages can serve it. The root
   `PRIVACY.md` stays as the canonical source for the repo README; the
   `docs/privacy.md` copy is what the Chrome Web Store points at.

   ```powershell
   Copy-Item .\PRIVACY.md .\docs\privacy.md
   ```

   Re-copy on every edit, or add a tiny pre-commit hook later.

3. **Enable Pages.** In the GitHub repo:
   - Settings -> Pages
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`)
   - Folder: `/docs`
   - Save

4. **Wait ~1 minute** for the first build. GitHub shows the live URL on the
   Pages settings page once it deploys.

### URL to Register in the Chrome Web Store

Use this URL pattern in the "Privacy policy" field of the Chrome Web Store
developer dashboard:

```text
https://<github-username>.github.io/save-to-obsidian/privacy
```

GitHub Pages serves `docs/privacy.md` as `/privacy` (it strips the `.md`
extension and renders the Markdown with the default Jekyll theme). If
served at `/privacy.md` instead on your account, register that URL exactly
as it resolves in a private browser window. Confirm it loads before saving
the dashboard form.

### Optional Polish

- Add a minimal `docs/_config.yml` with `title: ChatGPT Obsidian Saver` for
  a cleaner page header.
- Add `docs/index.md` pointing at `privacy.md` and the GitHub repo so the
  root of the Pages site is not a 404.
- No custom domain is needed for store submission. Skip DNS work unless
  you already own a domain you want to use.

### Updating the Policy Later

1. Edit `PRIVACY.md` at the repo root (the canonical copy).
2. `Copy-Item .\PRIVACY.md .\docs\privacy.md`.
3. Commit and push. GitHub Pages redeploys automatically.
4. The Chrome Web Store URL does not change, so no dashboard update is
   required unless the file path changes.

## Cross-Reference: STORE_LISTING.md Pre-Publish Checklist

This file resolves the following items from `STORE_LISTING.md`:

- "Host `PRIVACY.md` at a public URL and use that URL in the Chrome Web
  Store dashboard." -> follow the steps above; paste the resulting
  `https://<github-username>.github.io/save-to-obsidian/privacy` URL
  into the dashboard's Privacy policy field.
- "Set Chrome Web Store privacy disclosures to match `PRIVACY.md`." ->
  mirror the "Data Handled" and "Data Not Collected" sections of the
  hosted privacy policy in the dashboard's Privacy practices form.
- "Choose and add an open-source license before publishing source
  publicly." -> resolved by the `LICENSE` file at the repo root (MIT).

Items still owned by the user and not covered here:

- "After publication assigns a stable extension ID, set helper
  `ALLOWED_EXTENSION_ORIGIN=chrome-extension://<published-extension-id>`
  in public setup docs." Update `README.md` and `SECURITY.md` once the
  store assigns the ID.
- "Create final screenshots from the packaged extension, not a
  development mock." Take screenshots from the loaded `dist` build, not
  the dev workspace.

## Submission Order

A clean sequence for the first submission:

1. Run `.\scripts\validate.ps1` and `.\scripts\package-extension.ps1`.
2. Push the public repo (with `LICENSE`, `PRIVACY.md`, `docs/privacy.md`).
3. Enable GitHub Pages and confirm the privacy URL loads.
4. Upload `dist\chatgpt-obsidian-saver-extension.zip` to the Chrome Web
   Store dashboard.
5. Paste the GitHub Pages privacy URL into the dashboard.
6. Fill in permission justifications from `STORE_LISTING.md`.
7. Upload final screenshots.
8. Submit for review.
9. When the store assigns an extension ID, update
   `ALLOWED_EXTENSION_ORIGIN` guidance in `README.md` and `SECURITY.md`,
   then push.
