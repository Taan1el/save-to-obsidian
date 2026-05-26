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
  if (!helperToken.value.trim()) {
    statusNode.textContent = "Helper token is required";
    return;
  }

  await chrome.storage.local.set({
    helperUrl: normalizedUrl,
    helperToken: helperToken.value.trim()
  });
  statusNode.textContent = "Settings saved";
}

saveButton.addEventListener("click", saveOptions);
loadOptions();
