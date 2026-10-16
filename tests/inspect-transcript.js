// Paste this read-only expression into Chrome DevTools on the failing chat.
// Only detached clones are modified; message content is not included in output.
(() => {
  const container = document.querySelector("[data-chatgpt-conversation-selection-target]");
  if (!container) return { error: "Transcript container not found" };
  const describe = (element) => element && ({
    tag: element.tagName,
    class: String(element.className),
    role: element.getAttribute("role"),
    testId: element.getAttribute("data-testid"),
    children: Array.from(element.children, (child) => child.tagName)
  });
  const visible = (element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
  };
  const headings = Array.from(container.querySelectorAll("h4.sr-only"));
  const remainder = container.cloneNode(true);
  const copies = remainder.querySelectorAll("h4.sr-only");
  const checks = headings.map((heading, index) => {
    const wrapper = heading.parentElement;
    const body = heading.nextElementSibling;
    const style = getComputedStyle(heading);
    const label = heading.textContent.trim();
    const failed = [];
    if (!["You said:", "ChatGPT said:"].includes(label)) failed.push("unrecognized speaker label");
    if (wrapper.tagName !== "DIV") failed.push("parent is not DIV");
    if (wrapper.children.length !== 2) failed.push("parent does not have exactly two element children");
    if (wrapper.firstElementChild !== heading) failed.push("heading is not first element child");
    if (body?.tagName !== "DIV") failed.push("next element sibling is not DIV");
    if (style.display === "none" || style.visibility === "hidden") failed.push("heading CSS hides it");
    if (body && !visible(body)) failed.push("body has no visible bounding box");
    if (heading.closest("pre, code, blockquote")) failed.push("heading is in a quotation or code");
    if (body?.querySelector("h4.sr-only")) failed.push("body contains another speaker-like heading");
    if (Array.from(wrapper.childNodes).some((node) => node.nodeType === 3 && node.textContent.trim())) {
      failed.push("parent has extra direct text");
    }
    if (body && !(body.innerText || "").trim()) failed.push("empty body innerText");
    copies[index].parentElement.replaceChildren();
    return {
      index, label: failed.includes("unrecognized speaker label") ? "<unrecognized>" : label, failed,
      headingCSS: { display: style.display, visibility: style.visibility },
      parent: describe(wrapper), body: describe(body),
      bodyChildren: body ? Array.from(body.children, describe) : []
    };
  });
  const isMetadata = (text) => /^(?:Today\s*2:02\s*AM|Today|2:02\s*AM|Memory updated)$/i.test(text.trim());
  const metadata = Array.from(container.querySelectorAll("*")).filter((element) =>
    isMetadata(element.textContent) && !Array.from(element.children).some((child) => isMetadata(child.textContent))
  ).slice(0, 24).map((element) => {
    const ancestors = [];
    for (let parent = element.parentElement; parent && parent !== container && ancestors.length < 5; parent = parent.parentElement) {
      ancestors.push(describe(parent));
    }
    return {
      text: element.textContent.trim(), node: describe(element), ancestors,
      insideSpeakerBodies: headings.flatMap((heading, index) => heading.nextElementSibling?.contains(element) ? [index] : [])
    };
  });
  const unclaimedTextPresent = Boolean(remainder.textContent.trim());
  const unclaimedMetadata = {
    timestamp: /Today\s*2:02\s*AM/i.test(remainder.textContent),
    memory: remainder.textContent.includes("Memory updated")
  };
  const excludedUI = Array.from(remainder.querySelectorAll('[role="separator"] time, button'))
    .filter((node) => !node.closest("pre, code, blockquote"));
  const excludedUIElements = excludedUI.map(describe);
  excludedUI.forEach((node) => node.remove());
  const unclaimedTextAfterUI = Boolean(remainder.textContent.trim());
  return {
    container: describe(container), checks, metadata,
    unclaimedTextPresent, unclaimedMetadata, excludedUIElements, unclaimedTextAfterUI,
    uiIsOnlyRejection: checks.length > 0 && checks.every((check) => check.failed.length === 0) && unclaimedTextPresent && !unclaimedTextAfterUI,
    legacyCounts: {
      authorRoles: document.querySelectorAll("[data-message-author-role]").length,
      articles: document.querySelectorAll("article").length
    }
  };
})()
