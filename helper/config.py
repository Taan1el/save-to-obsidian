from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


AI_PROVIDERS = {"ollama", "openai", "anthropic", "gemini", "openai-compatible"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    vault_path: Path
    chatgpt_folder: str
    helper_token: str
    ai_provider: str
    ollama_base_url: str
    ollama_model: str
    openai_api_key: str | None
    openai_model: str
    anthropic_api_key: str | None
    anthropic_model: str
    gemini_api_key: str | None
    gemini_model: str
    openai_compatible_api_key: str | None
    openai_compatible_base_url: str
    openai_compatible_model: str
    helper_dev: bool
    allowed_extension_origin: str | None
    max_request_bytes: int

    @property
    def output_dir(self) -> Path:
        return self.vault_path / self.chatgpt_folder


def load_settings() -> Settings:
    _load_env_file(ENV_PATH)

    vault_path_raw = os.environ.get("OBSIDIAN_VAULT_PATH", "").strip()
    vault_path = Path(vault_path_raw).expanduser()
    helper_token = os.environ.get("HELPER_TOKEN", "")
    chatgpt_folder = os.environ.get("OBSIDIAN_CHATGPT_FOLDER", "ChatGPT")
    ai_provider = os.environ.get("AI_PROVIDER", "openai").strip().lower()
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    openai_compatible_base_url = os.environ.get(
        "OPENAI_COMPATIBLE_BASE_URL",
        "http://127.0.0.1:1234/v1",
    ).rstrip("/")
    openai_compatible_model = os.environ.get("OPENAI_COMPATIBLE_MODEL", "")
    helper_dev = os.environ.get("HELPER_DEV", "0") == "1"
    allowed_extension_origin = os.environ.get("ALLOWED_EXTENSION_ORIGIN") or None
    max_request_bytes = int(os.environ.get("MAX_REQUEST_BYTES", "1000000"))

    if not vault_path_raw:
        raise RuntimeError("OBSIDIAN_VAULT_PATH is required.")
    if not helper_token:
        raise RuntimeError("HELPER_TOKEN is required.")
    if Path(chatgpt_folder).is_absolute() or ".." in Path(chatgpt_folder).parts:
        raise RuntimeError("OBSIDIAN_CHATGPT_FOLDER must be a relative folder name.")
    if ai_provider not in AI_PROVIDERS:
        allowed = ", ".join(sorted(AI_PROVIDERS))
        raise RuntimeError(f"AI_PROVIDER must be one of: {allowed}.")

    return Settings(
        vault_path=vault_path.resolve(),
        chatgpt_folder=chatgpt_folder,
        helper_token=helper_token,
        ai_provider=ai_provider,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
        openai_model=openai_model,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        anthropic_model=anthropic_model,
        gemini_api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or None,
        gemini_model=gemini_model,
        openai_compatible_api_key=os.environ.get("OPENAI_COMPATIBLE_API_KEY") or None,
        openai_compatible_base_url=openai_compatible_base_url,
        openai_compatible_model=openai_compatible_model,
        helper_dev=helper_dev,
        allowed_extension_origin=allowed_extension_origin,
        max_request_bytes=max_request_bytes,
    )
