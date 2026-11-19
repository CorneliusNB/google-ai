"""Offline coverage for multilingual README navigation and safety-critical guidance."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("vi", "zh-CN", "ja", "ko", "es", "fr")
DOCS = ("README.md",) + tuple(f"README.{locale}.md" for locale in LANGUAGES)

REQUIRED_REFERENCES = (
    "README.md",
    "README.vi.md",
    "README.zh-CN.md",
    "README.ja.md",
    "README.ko.md",
    "README.es.md",
    "README.fr.md",
)
REQUIRED_LINKS = ("DISCLAIMER.md", "SECURITY.md", "CONTRIBUTING.md",
                  "THIRD_PARTY_NOTICES.md", "docs/DETAILED-GUIDE.md",
                  "https://www.mumuplayer.com/download/",
                  "https://github.com/hoangsvit/google-ai/wiki/Install")
REQUIRED_COMMANDS = (".\\run-all.ps1", "-Step 1", "-Step 2", "-Step 3",
                     "-Step 4", "-Step 5", "-AllStages", "-StartStep 3")
REQUIRED_IDENTIFIERS = ("Frida 16.5.9", "Google Play", "MuMuPlayer",
                        "Verified in Google Play", "David Nguyen (@hoangsvit)")


class ReadmeLocalesTests(unittest.TestCase):
    def test_language_switcher_points_to_every_existing_readme(self):
        for path in DOCS:
            with self.subTest(file=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                for reference in REQUIRED_REFERENCES:
                    self.assertIn(reference if reference != path else "English"
                                  if path == "README.md" else reference.split(".")[1],
                                  text)
                self.assertEqual(text.count("```") % 2, 0, path)

    def test_important_safety_and_operational_details_are_present(self):
        for path in DOCS:
            with self.subTest(file=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                for reference in REQUIRED_LINKS + REQUIRED_COMMANDS + REQUIRED_IDENTIFIERS:
                    self.assertIn(reference, text)

    def test_local_markdown_links_resolve(self):
        for path in DOCS:
            source = ROOT / path
            text = source.read_text(encoding="utf-8")
            links = re.findall(r"(?<!!)\\[[^]]+\\]\\(([^)]+)\\)", text)
            for target in links:
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                clean = target.split("#", 1)[0]
                with self.subTest(file=path, link=clean):
                    self.assertTrue((source.parent / clean).is_file())


if __name__ == "__main__":
    unittest.main()
