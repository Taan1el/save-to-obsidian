"""Run content-script regressions in Chrome without extra automation packages."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_result = False
        self.result = ""

    def handle_starttag(self, tag, attrs):
        if tag == "pre" and dict(attrs).get("id") == "results":
            self.in_result = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_result = False

    def handle_data(self, data):
        if self.in_result:
            self.result += data


class ContentExtractionTestCase(unittest.TestCase):
    def test_browser_regressions(self):
        candidates = [shutil.which(name) for name in ("google-chrome", "chromium", "chrome", "brave")]
        for root in (os.environ.get("PROGRAMFILES"), os.environ.get("LOCALAPPDATA")):
            if root:
                candidates.extend([
                    str(Path(root) / "Google/Chrome/Application/chrome.exe"),
                    str(Path(root) / "BraveSoftware/Brave-Browser/Application/brave.exe"),
                ])
        browser = next((path for path in candidates if path and Path(path).is_file()), None)
        if not browser:
            self.skipTest("Chrome, Chromium, or Brave is required for DOM extraction regressions")

        fixture = Path(__file__).with_name("content-extraction.html").resolve()
        with tempfile.TemporaryDirectory(prefix="content-extraction-") as profile:
            result = subprocess.run(
                [browser, "--headless=new", "--disable-gpu", "--disable-background-networking",
                 "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
                 "--allow-file-access-from-files", "--dump-dom", fixture.as_uri()],
                capture_output=True, text=True, encoding="utf-8", timeout=45,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        parser = ResultParser()
        parser.feed(result.stdout)
        self.assertNotEqual(parser.result, "pending", "Browser did not run the fixture")
        self.assertTrue(parser.result, "Browser did not return fixture results")
        cases = json.loads(parser.result)
        self.assertTrue(cases, "Fixture did not execute any cases")
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertIsNone(case.get("error"), case.get("error"))
        if any(case.get("error") for case in cases):
            return

        # Exercise the existing Save full schema and rendering with browser output.
        # This uses no helper server, configured vault, or network requests.
        from helper.markdown_writer import render_markdown, render_messages
        from helper.models import SaveRequest

        archive = next(case for case in cases if "conversation" in case)
        payload = SaveRequest(mode="full", **archive["conversation"])
        self.assertEqual(len(payload.messages), 1)
        self.assertEqual(payload.messages[0].role, "system")
        markdown = render_markdown(
            title=payload.title,
            chat_url=payload.chat_url,
            mode=payload.mode,
            body=render_messages(payload.messages),
        )
        self.assertIn("Unattributed ChatGPT transcript", markdown)
        self.assertIn("not an original conversation message", markdown)
        self.assertTrue(markdown.endswith(archive["transcript"] + "\n"))
        self.assertNotIn("## User\n", markdown)
        self.assertNotIn("## Assistant\n", markdown)

        attributed = next(case for case in cases if "attributedConversation" in case)
        payload = SaveRequest(mode="full", **attributed["attributedConversation"])
        self.assertEqual([message.model_dump() for message in payload.messages], attributed["expectedMessages"])
        body = render_messages(payload.messages)
        self.assertEqual(body.count("## User\n"), 2)
        self.assertEqual(body.count("## Assistant\n"), 2)
        for message in payload.messages:
            self.assertEqual(body.count(message.content), 1)

        ui_case = next(case for case in cases if "uiConversation" in case)
        payload = SaveRequest(mode="full", **ui_case["uiConversation"])
        self.assertEqual([message.model_dump() for message in payload.messages], ui_case["expectedMessages"])
        body = render_messages(payload.messages)
        self.assertNotIn("Today 2:02 AM", body)
        self.assertNotIn("Memory updated", body)
        self.assertNotIn("Unattributed ChatGPT transcript", body)
        self.assertEqual(body.count("## User\n"), 2)
        self.assertEqual(body.count("## Assistant\n"), 2)


if __name__ == "__main__":
    unittest.main()
