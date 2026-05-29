const DEFAULT_HELPER_URL = "http://127.0.0.1:8766";
const els = {
  statusDot: document.getElementById("statusDot"),
  helperText: document.getElementById("helperText"),
  messageBox: document.getElementById("messageBox"),
  buttons: Array.from(document.querySelectorAll("[data-mode]")),
  openOptions: document.getElementById("openOptions")
};

let helperBaseUrl = DEFAULT_HELPER_URL;
let helperToken = "";
let helperReady = false;

init();

async function init() {
  const config = await getConfig();
  helperBaseUrl = config.helperUrl;
  helperToken = config.helperToken;
  await checkHelper();

  els.buttons.forEach((button) => {
    button.addEventListener("click", () => saveConversation(button.dataset.mode, button));
  });

  els.openOptions.addEventListener("click", () => {
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    }
  });
}

async function getConfig() {
  const local = await chrome.storage.local.get({
    helperUrl: DEFAULT_HELPER_URL,
    helperToken: ""
  });

  return {
    helperUrl: normalizeBaseUrl(local.helperUrl || DEFAULT_HELPER_URL),
    helperToken: local.helperToken || ""
  };
}

function normalizeBaseUrl(url) {
  return String(url).trim().replace(/\/+$/, "");
}

function validHelperUrl(url) {
  return /^http:\/\/(127\.0\.0\.1|localhost):\d+$/i.test(url);
}

async function checkHelper() {
  setHelperState("checking");

  try {
    if (!validHelperUrl(helperBaseUrl)) {
      throw new Error("Invalid helper URL");
    }

    const response = await chrome.runtime.sendMessage({
      type: "health-check",
      helperUrl: helperBaseUrl
    });

    if (!response?.ok) throw new Error("Helper not running");

    helperReady = true;
    setHelperState("ready");
    if (helperToken) {
      const diagnostics = await chrome.runtime.sendMessage({
        type: "diagnostics",
        helperUrl: helperBaseUrl,
        helperToken
      });
      const provider = providerLabel(diagnostics?.body?.ai_provider);
      setMessage(`Ready - ${provider}`, "neutral");
    } else {
      setMessage("Set helper token in Options", "error");
    }
  } catch {
    helperReady = false;
    setHelperState("offline");
    setMessage("Helper not running", "error");
  }
}

async function saveConversation(mode, sourceButton) {
  clearButtonLoading();
  sourceButton.classList.add("is-loading");
  setMessage("Extracting conversation...", "working");

  try {
    if (!helperToken) {
      throw new Error("Set helper token in Options");
    }
    if (!validHelperUrl(helperBaseUrl)) {
      throw new Error("Invalid helper URL");
    }

    if (!helperReady) {
      await checkHelper();
      if (!helperReady) throw new Error("Helper not running");
    }

    const conversation = await extractConversationFromActiveTab();
    if (!conversation?.messages?.length) {
      throw new Error("Could not extract conversation");
    }

    setMessage("Saving to Obsidian...", "working");

    const response = await chrome.runtime.sendMessage({
      type: "save-conversation",
      helperUrl: helperBaseUrl,
      helperToken,
      mode,
      conversation
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Save failed");
    }

    setMessage(`Saved: ${response.filename || "conversation.md"}`, "success");
    setHelperState("ready");
  } catch (error) {
    const message = normalizeErrorMessage(error);
    setMessage(message, "error");

    if (message === "Helper not running") {
      helperReady = false;
      setHelperState("offline");
    }
  } finally {
    clearButtonLoading();
  }
}

async function extractConversationFromActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab?.id || !/^https:\/\/(chatgpt\.com|chat\.openai\.com)\//.test(tab.url || "")) {
    throw new Error("Could not extract conversation");
  }

  try {
    return await requestExtraction(tab.id);
  } catch (error) {
    if (!/Receiving end does not exist|Could not establish connection/i.test(error?.message || "")) {
      throw error;
    }
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
    return await requestExtraction(tab.id);
  }
}

function requestExtraction(tabId) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, { type: "extract-conversation" }, (response) => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
        return;
      }
      if (!response?.ok) {
        reject(new Error(response?.error || "Could not extract conversation"));
        return;
      }
      resolve(response.conversation);
    });
  });
}

function providerLabel(provider) {
  const labels = {
    ollama: "Local Ollama",
    openai: "OpenAI",
    anthropic: "Anthropic",
    gemini: "Gemini",
    "openai-compatible": "OpenAI-compatible"
  };
  return labels[provider] || "AI provider";
}

function normalizeErrorMessage(error) {
  const raw = error?.message || "";

  if (raw.includes("Set helper token")) return "Set helper token in Options";
  if (raw.includes("Invalid helper URL")) return "Invalid helper URL";
  if (raw.includes("Unauthorized")) return "Unauthorized";
  if (raw.includes("Could not extract conversation") || raw.includes("Receiving end does not exist") || raw.includes("Could not establish connection")) {
    return "Could not extract conversation";
  }
  if (raw.includes("Helper not running") || raw.includes("Failed to fetch")) return "Helper not running";
  if (/(OPENAI|ANTHROPIC|GEMINI|GOOGLE|OPENAI_COMPATIBLE)_API_KEY|OPENAI_COMPATIBLE_MODEL/.test(raw)) return raw;

  return raw || "Save failed";
}

function setHelperState(state) {
  els.statusDot.classList.remove("is-ready", "is-offline", "is-checking");

  if (state === "ready") {
    els.statusDot.classList.add("is-ready");
    els.helperText.textContent = "Helper ready";
    return;
  }

  if (state === "offline") {
    els.statusDot.classList.add("is-offline");
    els.helperText.textContent = "Helper offline";
    return;
  }

  els.statusDot.classList.add("is-checking");
  els.helperText.textContent = "Checking helper...";
}

function setMessage(text, tone = "neutral") {
  els.messageBox.textContent = text;
  els.messageBox.classList.remove("is-success", "is-error", "is-working");

  if (tone === "success") els.messageBox.classList.add("is-success");
  if (tone === "error") els.messageBox.classList.add("is-error");
  if (tone === "working") els.messageBox.classList.add("is-working");
}

function clearButtonLoading() {
  els.buttons.forEach((button) => button.classList.remove("is-loading"));
}
