const TOKEN_HEADER = "X-Obsidian-Saver-Token";

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request?.type === "health-check") {
    healthCheck(request).then(sendResponse);
    return true;
  }

  if (request?.type === "diagnostics") {
    diagnostics(request).then(sendResponse);
    return true;
  }

  if (request?.type === "save-conversation") {
    saveConversation(request).then(sendResponse);
    return true;
  }

  return false;
});

async function healthCheck(request) {
  try {
    const response = await fetch(`${request.helperUrl}/health`, {
      method: "GET",
      cache: "no-store"
    });
    return { ok: response.ok };
  } catch {
    return { ok: false, error: "Helper not running" };
  }
}

async function diagnostics(request) {
  try {
    const response = await fetch(`${request.helperUrl}/diagnostics`, {
      method: "GET",
      cache: "no-store",
      headers: {
        [TOKEN_HEADER]: request.helperToken
      }
    });
    const body = await safeJson(response);
    return { ok: response.ok, body };
  } catch {
    return { ok: false };
  }
}

async function saveConversation(request) {
  try {
    const response = await fetch(`${request.helperUrl}/save`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        [TOKEN_HEADER]: request.helperToken
      },
      body: JSON.stringify({ ...request.conversation, mode: request.mode })
    });

    const body = await safeJson(response);
    if (response.status === 401 || response.status === 403) {
      return { ok: false, error: "Unauthorized" };
    }
    if (!response.ok) {
      return { ok: false, error: body?.detail || "Save failed" };
    }
    return { ok: true, filename: body?.filename || "conversation.md", path: body?.path };
  } catch (error) {
    if (/failed to fetch/i.test(error?.message || "")) {
      return { ok: false, error: "Helper not running" };
    }
    return { ok: false, error: error?.message || "Save failed" };
  }
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
