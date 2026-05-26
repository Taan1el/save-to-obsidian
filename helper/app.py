from __future__ import annotations

import secrets
import asyncio
import json
import re
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from fastapi import FastAPI, Header, HTTPException, Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .markdown_writer import render_markdown, render_messages, write_note
from .models import SaveRequest, SaveResponse


TOKEN_HEADER = "X-Obsidian-Saver-Token"

settings_at_startup = load_settings()
app = FastAPI(
    title="ChatGPT Obsidian Saver Helper",
    version="0.1.0",
    docs_url="/docs" if settings_at_startup.helper_dev else None,
    redoc_url="/redoc" if settings_at_startup.helper_dev else None,
    openapi_url="/openapi.json" if settings_at_startup.helper_dev else None,
)

if settings_at_startup.allowed_extension_origin:
    allow_origin_regex = f"^{re.escape(settings_at_startup.allowed_extension_origin)}$"
else:
    allow_origin_regex = r"^(chrome-extension://.*|http://127\.0\.0\.1(:\d+)?|http://localhost(:\d+)?)$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[TOKEN_HEADER, "Content-Type"],
)


@app.middleware("http")
async def reject_oversized_requests(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        try:
            request_bytes = int(content_length) if content_length else 0
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header."},
            )
        if request_bytes > settings_at_startup.max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large."},
            )
    return await call_next(request)


def require_token(token: str | None) -> None:
    settings = load_settings()
    if not token or not secrets.compare_digest(token, settings.helper_token):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def build_ai_body(payload: SaveRequest, instruction: str) -> str:
    settings = load_settings()
    transcript = render_messages(payload.messages)
    prompt = (
        "Create concise, clean Markdown for an Obsidian note. "
        "Do not add YAML frontmatter.\n\n"
        f"{instruction}\n\nConversation:\n\n{transcript}"
    )

    if settings.ai_provider == "ollama":
        return await build_ollama_body(prompt)
    if settings.ai_provider == "anthropic":
        return await build_anthropic_body(payload, prompt)
    if settings.ai_provider == "gemini":
        return await build_gemini_body(payload, prompt)
    if settings.ai_provider == "openai-compatible":
        return await build_openai_compatible_body(payload, prompt)

    return await build_openai_body(payload, prompt)


def missing_key_error(payload: SaveRequest, env_name: str) -> HTTPException:
    mode_label = "Summary" if payload.mode == "summary" else "Main idea"
    return HTTPException(
        status_code=400,
        detail=f"{mode_label} requires {env_name} in the local helper.",
    )


async def build_openai_body(payload: SaveRequest, prompt: str) -> str:
    settings = load_settings()
    if not settings.openai_api_key:
        raise missing_key_error(payload, "OPENAI_API_KEY")

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="OpenAI package is not installed.") from exc

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.output_text.strip()


async def build_openai_compatible_body(payload: SaveRequest, prompt: str) -> str:
    settings = load_settings()
    if not settings.openai_compatible_api_key:
        raise missing_key_error(payload, "OPENAI_COMPATIBLE_API_KEY")
    if not settings.openai_compatible_model:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_COMPATIBLE_MODEL is required when AI_PROVIDER=openai-compatible.",
        )

    return await asyncio.to_thread(
        _call_openai_compatible,
        settings.openai_compatible_base_url,
        settings.openai_compatible_api_key,
        settings.openai_compatible_model,
        prompt,
    )


async def build_anthropic_body(payload: SaveRequest, prompt: str) -> str:
    settings = load_settings()
    if not settings.anthropic_api_key:
        raise missing_key_error(payload, "ANTHROPIC_API_KEY")

    return await asyncio.to_thread(
        _call_anthropic,
        settings.anthropic_api_key,
        settings.anthropic_model,
        prompt,
    )


async def build_gemini_body(payload: SaveRequest, prompt: str) -> str:
    settings = load_settings()
    if not settings.gemini_api_key:
        raise missing_key_error(payload, "GEMINI_API_KEY")

    return await asyncio.to_thread(
        _call_gemini,
        settings.gemini_api_key,
        settings.gemini_model,
        prompt,
    )


async def build_ollama_body(prompt: str) -> str:
    settings = load_settings()
    return await asyncio.to_thread(_call_ollama, settings.ollama_base_url, settings.ollama_model, prompt)


def _post_json(url: str, body: dict, headers: dict[str, str], timeout: int = 180) -> dict:
    request = UrlRequest(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") or str(exc)
        raise HTTPException(status_code=400, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(status_code=400, detail=f"AI provider request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider timed out while generating.") from exc


def _call_openai_compatible(base_url: str, api_key: str, model: str, prompt: str) -> str:
    payload = _post_json(
        f"{base_url}/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        {"Authorization": f"Bearer {api_key}"},
    )
    text = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not text:
        raise HTTPException(status_code=500, detail="OpenAI-compatible provider returned an empty response.")
    return str(text).strip()


def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    payload = _post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        },
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    parts = payload.get("content", [])
    text = "\n".join(str(part.get("text", "")).strip() for part in parts if part.get("type") == "text")
    if not text:
        raise HTTPException(status_code=500, detail="Anthropic returned an empty response.")
    return text.strip()


def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    payload = _post_json(
        url,
        {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}},
        {"x-goog-api-key": api_key},
    )
    candidates = payload.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "\n".join(str(part.get("text", "")).strip() for part in parts if part.get("text"))
    if not text:
        raise HTTPException(status_code=500, detail="Gemini returned an empty response.")
    return text.strip()


def _call_ollama(base_url: str, model: str, prompt: str) -> str:
    request = UrlRequest(
        f"{base_url}/api/generate",
        data=json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") or str(exc)
        raise HTTPException(
            status_code=400,
            detail=f"Ollama request failed for model {model}: {detail}",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ollama is not running. Install Ollama, run "
                f"`ollama pull {model}`, then start Ollama."
            ),
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Ollama timed out while generating.") from exc

    text = str(payload.get("response", "")).strip()
    if not text:
        raise HTTPException(status_code=500, detail="Ollama returned an empty response.")
    return text


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/diagnostics")
def diagnostics(x_obsidian_saver_token: str | None = Header(default=None, alias=TOKEN_HEADER)) -> dict[str, str | bool]:
    require_token(x_obsidian_saver_token)
    settings = load_settings()
    return {
        "ok": True,
        "bind": "127.0.0.1",
        "output_dir": str(settings.output_dir),
        "ai_provider": settings.ai_provider,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "openai_configured": bool(settings.openai_api_key),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
        "openai_compatible_configured": bool(settings.openai_compatible_api_key),
    }


@app.post("/save", response_model=SaveResponse)
async def save(
    payload: SaveRequest,
    x_obsidian_saver_token: str | None = Header(default=None, alias=TOKEN_HEADER),
) -> SaveResponse:
    require_token(x_obsidian_saver_token)
    settings = load_settings()
    output_dir = settings.output_dir.resolve()
    vault_path = settings.vault_path.resolve()
    if vault_path != output_dir and vault_path not in output_dir.parents:
        raise HTTPException(status_code=500, detail="Configured output folder is outside the vault.")

    if payload.mode == "full":
        body = render_messages(payload.messages)
    elif payload.mode == "summary":
        body = await build_ai_body(
            payload,
            "Summarize this ChatGPT conversation. Keep the useful context, decisions, and next steps.",
        )
    else:
        body = await build_ai_body(
            payload,
            "Extract the core idea, key points, and action items from this ChatGPT conversation.",
        )

    markdown = render_markdown(
        title=payload.title,
        chat_url=payload.chat_url,
        mode=payload.mode,
        body=body,
    )
    note_path = write_note(output_dir, payload.title, markdown)
    return SaveResponse(ok=True, filename=note_path.name, path=str(note_path))
