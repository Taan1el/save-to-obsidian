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

// The observed transcript DOM pairs H4.sr-only speaker headings with a sibling
// content DIV. Outer nesting differs between roles, so inspect only that pair.
// Return no attribution unless every pair and the complete transcript validate.
function extractFromTranscriptHeadings(container) {
  const headings = Array.from(container.querySelectorAll("h4.sr-only"));
  if (headings.length === 0) return [];
  const remainder = container.cloneNode(true);
  const copiedHeadings = remainder.querySelectorAll("h4.sr-only");
  const messages = [];

  for (let i = 0; i < headings.length; i++) {
    const heading = headings[i];
    const label = heading.textContent.trim();
    const role = label === "You said:" ? "user" : label === "ChatGPT said:" ? "assistant" : null;
    const wrapper = heading.parentElement;
    const body = heading.nextElementSibling;
    const style = window.getComputedStyle(heading);
    if (!role || wrapper.tagName !== "DIV" || wrapper.children.length !== 2 ||
        wrapper.firstElementChild !== heading || body?.tagName !== "DIV" ||
        style.display === "none" || style.visibility === "hidden" || !visible(body) ||
        heading.closest("pre, code, blockquote") || body.querySelector("h4.sr-only") ||
        Array.from(wrapper.childNodes).some((node) => node.nodeType === 3 && node.textContent.trim())) {
      return [];
    }
    const content = (body.innerText || "").replace(/\r\n?/g, "\n").trim();
    if (!content) return [];
    messages.push({ role, content });
    copiedHeadings[i].parentElement.replaceChildren();
  }

  // Message bodies have already been removed from this detached clone. Exclude
  // the observed date separators and auxiliary buttons only from what remains;
  // never strip their text from actual messages or from quoted examples.
  remainder.querySelectorAll('[role="separator"] time, button').forEach((node) => {
    if (!node.closest("pre, code, blockquote")) node.remove();
  });
  // Recheck after UI removal: any other unclaimed text still makes attribution
  // uncertain and must preserve the complete visible transcript as an archive.
  return remainder.textContent.trim() ? [] : messages;
}

// Newer ChatGPT views expose a selection/transcript container. Speaker labels in
// text alone never establish boundaries; ambiguous DOM stays as one archive.
function extractFromTranscriptContainer() {
  const transcripts = Array.from(
    document.querySelectorAll("[data-chatgpt-conversation-selection-target]")
  ).filter(visible)
    .map((container) => ({ container, text: (container.innerText || "").replace(/\r\n?/g, "\n").trim() }))
    .filter(({ text }) => text);
  const uniqueTranscripts = Array.from(new Set(transcripts.map(({ text }) => text)));

  if (uniqueTranscripts.length === 0) return [];
  if (uniqueTranscripts.length > 1) {
    throw new Error("Could not extract conversation: multiple different transcript containers were found");
  }

  const candidates = transcripts.map(({ container }) => extractFromTranscriptHeadings(container));
  if (candidates[0].length && candidates.every((messages) => JSON.stringify(messages) === JSON.stringify(candidates[0]))) {
    return candidates[0];
  }

  // The existing helper accepts user/assistant/system records only. Use system
  // solely as an explicitly labeled archive envelope, never as inferred authorship.
  const content = "Unattributed ChatGPT transcript. Message boundaries and authorship could not be verified. " +
    "This system record is an archive envelope, not an original conversation message.\n\n" + uniqueTranscripts[0];
  // Match the helper's per-record limit without splitting or silently truncating.
  if (Array.from(content).length > 50_000) {
    throw new Error("Complete transcript exceeds the helper's 50,000-character limit for one archive record.");
  }
  return [{ role: "system", content }];
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
  if (messages.length === 0) {
    messages = extractFromTranscriptContainer();
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
