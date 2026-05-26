from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .models import ChatMessage, SaveMode


MAX_TITLE_WORDS = 8


def escape_yaml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", " ").replace("\n", " ")


def sanitize_filename_part(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        return "chatgpt-conversation"
    words = value.split("-")[:MAX_TITLE_WORDS]
    return "-".join(words)[:80].strip("-") or "chatgpt-conversation"


def ensure_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    if parent_resolved != child_resolved and parent_resolved not in child_resolved.parents:
        raise ValueError("Refusing to write outside configured Obsidian folder.")


def unique_note_path(output_dir: Path, title: str, created: date | None = None) -> Path:
    created = created or date.today()
    stem = f"{created.isoformat()}-{sanitize_filename_part(title)}"
    candidate = output_dir / f"{stem}.md"
    suffix = 2
    while candidate.exists():
        candidate = output_dir / f"{stem}-{suffix}.md"
        suffix += 1
    ensure_inside(candidate, output_dir)
    return candidate


def role_heading(role: str) -> str:
    return {
        "user": "User",
        "assistant": "Assistant",
        "system": "System",
    }.get(role, role.title())


def clean_content(content: str) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = [line.rstrip() for line in content.split("\n")]
    return "\n".join(lines).strip()


def render_messages(messages: list[ChatMessage]) -> str:
    blocks: list[str] = []
    for message in messages:
        content = clean_content(message.content)
        if not content:
            continue
        blocks.append(f"## {role_heading(message.role)}\n\n{content}")
    return "\n\n".join(blocks)


def render_markdown(
    *,
    title: str,
    chat_url: str,
    mode: SaveMode,
    body: str,
    created: date | None = None,
) -> str:
    created = created or date.today()
    safe_title = title.strip() or "ChatGPT conversation"
    safe_body = body.strip() or "_No content extracted._"

    return (
        "---\n"
        f'title: "{escape_yaml(safe_title)}"\n'
        "source: ChatGPT\n"
        f"created: {created.isoformat()}\n"
        "tags: [chatgpt]\n"
        f'chat_url: "{escape_yaml(chat_url)}"\n'
        f"mode: {mode}\n"
        "---\n\n"
        f"# {safe_title}\n\n"
        f"{safe_body}\n"
    )


def write_note(output_dir: Path, title: str, markdown: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_inside(output_dir, output_dir)
    note_path = unique_note_path(output_dir, title)
    note_path.write_text(markdown, encoding="utf-8", newline="\n")
    return note_path
