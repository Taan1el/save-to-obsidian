function textFromElement(element) {
  return (element.innerText || element.textContent || "")
    .replace(/\u00a0/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function visible(element) {
  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);
  return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
}

function titleFromPage(messages) {
  const documentTitle = document.title
    .replace(/^ChatGPT\s*[-|]\s*/i, "")
    .replace(/\s*[-|]\s*ChatGPT$/i, "")
    .trim();

  if (documentTitle && documentTitle.toLowerCase() !== "chatgpt") {
    return documentTitle;
  }

  const firstUser = messages.find((message) => message.role === "user");
  if (firstUser) {
    return firstUser.content.split(/\s+/).slice(0, 8).join(" ");
  }

  return "ChatGPT conversation";
}

function roleFromArticle(article) {
  const explicitAuthor = article.getAttribute("data-message-author-role");
  if (explicitAuthor === "user" || explicitAuthor === "assistant") {
    return explicitAuthor;
  }

  const authorNode = article.querySelector("[data-message-author-role]");
  const nestedAuthor = authorNode?.getAttribute("data-message-author-role");
  if (nestedAuthor === "user" || nestedAuthor === "assistant") {
    return nestedAuthor;
  }

  const aria = (article.getAttribute("aria-label") || "").toLowerCase();
  if (aria.includes("user")) return "user";
  if (aria.includes("assistant") || aria.includes("chatgpt")) return "assistant";

  const text = textFromElement(article).toLowerCase();
  if (text.startsWith("you said:")) return "user";
  if (text.startsWith("chatgpt said:")) return "assistant";

  return null;
}

function contentFromArticle(article) {
  const contentSelectors = [
    ".markdown",
    "[data-message-content]",
    ".whitespace-pre-wrap",
    "[class*='message-content']"
  ];

  for (const selector of contentSelectors) {
    const node = article.querySelector(selector);
    if (node && visible(node)) {
      const text = textFromElement(node);
      if (text) return text;
    }
  }

  return textFromElement(article)
    .replace(/^(You said:|ChatGPT said:)\s*/i, "")
    .trim();
}

function extractFromArticles() {
  const articles = Array.from(document.querySelectorAll("article")).filter(visible);
  const messages = [];

  for (const article of articles) {
    const role = roleFromArticle(article);
    const content = contentFromArticle(article);
    if (!role || !content) continue;
    messages.push({ role, content });
  }

  return messages;
}

function extractFromDataAttributes() {
  const nodes = Array.from(document.querySelectorAll("[data-message-author-role]")).filter(visible);
  const messages = [];

  for (const node of nodes) {
    const role = node.getAttribute("data-message-author-role");
    if (role !== "user" && role !== "assistant") continue;
    const container = node.closest("article") || node;
    const content = contentFromArticle(container);
    if (content) messages.push({ role, content });
  }

  return messages;
}

function dedupeAdjacent(messages) {
  const cleaned = [];
  for (const message of messages) {
    const previous = cleaned[cleaned.length - 1];
    if (previous && previous.role === message.role && previous.content === message.content) {
      continue;
    }
    cleaned.push(message);
  }
  return cleaned;
}

// ChatGPT DOM changes frequently. Keep all selectors in this function and its helpers.
function extractConversation() {
  let messages = extractFromDataAttributes();
  if (messages.length === 0) {
    messages = extractFromArticles();
  }

  messages = dedupeAdjacent(messages)
    .map((message) => ({ role: message.role, content: message.content.trim() }))
    .filter((message) => message.content.length > 0);

  if (messages.length === 0) {
    throw new Error("Could not extract conversation");
  }

  return {
    chat_url: window.location.href,
    title: titleFromPage(messages),
    messages
  };
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request?.type !== "extract-conversation") {
    return false;
  }

  try {
    sendResponse({ ok: true, conversation: extractConversation() });
  } catch (error) {
    sendResponse({ ok: false, error: error.message || "Could not extract conversation" });
  }
  return true;
});
