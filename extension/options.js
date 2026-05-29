const helperUrl = document.getElementById("helper-url");
const helperToken = document.getElementById("helper-token");
const statusNode = document.getElementById("status");
const saveButton = document.getElementById("save-options");

async function loadOptions() {
  const stored = await chrome.storage.local.get({
    helperUrl: "http://127.0.0.1:8766",
    helperToken: ""
  });
  helperUrl.value = stored.helperUrl;
  helperToken.value = stored.helperToken;
}

async function saveOptions() {
  const normalizedUrl = helperUrl.value.trim().replace(/\/+$/, "");
  if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/i.test(normalizedUrl)) {
    statusNode.textContent = "Use a local helper URL like http://127.0.0.1:8766";
    return;
  }

  // Drop any whitespace a paste may introduce.
  const cleanedToken = helperToken.value.replace(/\s+/g, "");
  if (!cleanedToken) {
    statusNode.textContent = "Helper token is required";
    return;
  }
  // The helper token is base64url/hex. Anything else (smart punctuation like an
  // en-dash, or a zero-width character) cannot be sent in an HTTP header.
  if (!/^[A-Za-z0-9_-]+$/.test(cleanedToken)) {
    statusNode.textContent = "Token has invalid characters. Re-copy it as plain text.";
    return;
  }

  helperToken.value = cleanedToken;
  await chrome.storage.local.set({
    helperUrl: normalizedUrl,
    helperToken: cleanedToken
  });
  statusNode.textContent = "Settings saved";
}

saveButton.addEventListener("click", saveOptions);
loadOptions();
