import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("OBSIDIAN_VAULT_PATH", tempfile.gettempdir())
os.environ.setdefault("OBSIDIAN_CHATGPT_FOLDER", "ChatGPT")
os.environ.setdefault("HELPER_TOKEN", "test-token")
os.environ.setdefault("AI_PROVIDER", "ollama")
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:1")
os.environ.setdefault("OLLAMA_MODEL", "llama3.2")

from helper.app import TOKEN_HEADER, app
from helper.config import load_settings
from helper.markdown_writer import sanitize_filename_part, unique_note_path


class HelperTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ["OBSIDIAN_VAULT_PATH"] = self.tmp.name
        os.environ["OBSIDIAN_CHATGPT_FOLDER"] = "ChatGPT"
        os.environ["HELPER_TOKEN"] = "test-token"
        os.environ["AI_PROVIDER"] = "ollama"
        os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
        os.environ["OLLAMA_MODEL"] = "llama3.2"
        for key in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "OPENAI_COMPATIBLE_API_KEY",
            "OPENAI_COMPATIBLE_MODEL",
        ):
            os.environ.pop(key, None)
        self.client = TestClient(app)
        self.payload = {
            "mode": "full",
            "chat_url": "https://chatgpt.com/c/example",
            "title": "Launch Readiness / Path Traversal",
            "messages": [
                {"role": "user", "content": "Save this conversation."},
                {"role": "assistant", "content": "Saved as Markdown."},
            ],
        }

    def auth_headers(self) -> dict[str, str]:
        return {TOKEN_HEADER: "test-token"}

    def test_health_reports_local_output_and_ai_provider(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertNotIn("output_dir", body)

        diagnostics = self.client.get("/diagnostics", headers=self.auth_headers())
        self.assertEqual(diagnostics.status_code, 200)
        self.assertEqual(diagnostics.json()["bind"], "127.0.0.1")
        self.assertEqual(diagnostics.json()["ai_provider"], "ollama")

    def test_save_requires_token(self) -> None:
        response = self.client.post("/save", json=self.payload)
        self.assertEqual(response.status_code, 401)

    def test_full_save_writes_markdown_inside_chatgpt_folder(self) -> None:
        response = self.client.post("/save", json=self.payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        note_path = Path(body["path"])
        self.assertTrue(note_path.exists())
        self.assertEqual(note_path.parent, Path(self.tmp.name) / "ChatGPT")
        text = note_path.read_text(encoding="utf-8")
        self.assertIn('source: ChatGPT', text)
        self.assertIn("mode: full", text)
        self.assertIn("## User", text)
        self.assertIn("## Assistant", text)

    def test_duplicate_filename_adds_numeric_suffix(self) -> None:
        output_dir = Path(self.tmp.name) / "ChatGPT"
        output_dir.mkdir()
        first = unique_note_path(output_dir, "Duplicate")
        first.write_text("x", encoding="utf-8")
        second = unique_note_path(output_dir, "Duplicate")
        self.assertTrue(second.name.endswith("-2.md"))

    def test_filename_sanitization_blocks_path_traversal_characters(self) -> None:
        self.assertEqual(sanitize_filename_part("../../Windows/System32"), "windowssystem32")

    def test_summary_uses_ollama_provider(self) -> None:
        payload = dict(self.payload, mode="summary")
        with patch("helper.app.build_ollama_body", return_value="## Summary\n\nDone.") as mocked:
            response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        mocked.assert_called_once()

    def test_summary_uses_anthropic_provider(self) -> None:
        os.environ["AI_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        payload = dict(self.payload, mode="summary")
        with patch("helper.app.build_anthropic_body", return_value="## Summary\n\nDone.") as mocked:
            response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        mocked.assert_called_once()

    def test_summary_uses_gemini_provider(self) -> None:
        os.environ["AI_PROVIDER"] = "gemini"
        os.environ["GEMINI_API_KEY"] = "test-gemini-key"
        payload = dict(self.payload, mode="summary")
        with patch("helper.app.build_gemini_body", return_value="## Summary\n\nDone.") as mocked:
            response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        mocked.assert_called_once()

    def test_summary_uses_openai_compatible_provider(self) -> None:
        os.environ["AI_PROVIDER"] = "openai-compatible"
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = "test-compatible-key"
        os.environ["OPENAI_COMPATIBLE_MODEL"] = "test-model"
        payload = dict(self.payload, mode="summary")
        with patch("helper.app.build_openai_compatible_body", return_value="## Summary\n\nDone.") as mocked:
            response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        mocked.assert_called_once()

    def test_openai_missing_key_error_when_selected(self) -> None:
        os.environ["AI_PROVIDER"] = "openai"
        payload = dict(self.payload, mode="summary")
        response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 400)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_cloud_provider_missing_key_errors_are_clear(self) -> None:
        cases = [
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("gemini", "GEMINI_API_KEY"),
            ("openai-compatible", "OPENAI_COMPATIBLE_API_KEY"),
        ]
        payload = dict(self.payload, mode="main-idea")
        for provider, env_name in cases:
            with self.subTest(provider=provider):
                os.environ["AI_PROVIDER"] = provider
                response = self.client.post("/save", json=payload, headers=self.auth_headers())
                self.assertEqual(response.status_code, 400)
                self.assertIn(env_name, response.json()["detail"])

    def test_openai_compatible_requires_model(self) -> None:
        os.environ["AI_PROVIDER"] = "openai-compatible"
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = "test-compatible-key"
        payload = dict(self.payload, mode="summary")
        response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 400)
        self.assertIn("OPENAI_COMPATIBLE_MODEL", response.json()["detail"])

    def test_rejects_too_many_messages(self) -> None:
        payload = dict(self.payload)
        payload["messages"] = [{"role": "user", "content": "x"} for _ in range(101)]
        response = self.client.post("/save", json=payload, headers=self.auth_headers())
        self.assertEqual(response.status_code, 422)

    def test_missing_vault_path_fails_hard(self) -> None:
        old_value = os.environ.get("OBSIDIAN_VAULT_PATH")
        os.environ["OBSIDIAN_VAULT_PATH"] = ""
        try:
            with self.assertRaisesRegex(RuntimeError, "OBSIDIAN_VAULT_PATH"):
                load_settings()
        finally:
            if old_value is None:
                os.environ.pop("OBSIDIAN_VAULT_PATH", None)
            else:
                os.environ["OBSIDIAN_VAULT_PATH"] = old_value

    def test_invalid_ai_provider_fails_hard(self) -> None:
        old_value = os.environ.get("AI_PROVIDER")
        os.environ["AI_PROVIDER"] = "bad-provider"
        try:
            with self.assertRaisesRegex(RuntimeError, "AI_PROVIDER"):
                load_settings()
        finally:
            if old_value is None:
                os.environ.pop("AI_PROVIDER", None)
            else:
                os.environ["AI_PROVIDER"] = old_value


if __name__ == "__main__":
    unittest.main()
