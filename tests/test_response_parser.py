from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "web"))

from app.response_parser import extract_output_text  # noqa: E402


class ResponseParserTests(unittest.TestCase):
    def test_direct_output_text(self) -> None:
        self.assertEqual(extract_output_text({"output_text": " Answer "}), "Answer")

    def test_nested_response_messages(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "First"},
                        {"type": "output_text", "text": "Second"},
                    ],
                }
            ]
        }
        self.assertEqual(extract_output_text(payload), "First\nSecond")

    def test_ignores_tool_items(self) -> None:
        payload = {"output": [{"type": "function_call", "name": "search"}]}
        self.assertEqual(extract_output_text(payload), "")

    def test_ignores_malformed_output_collection(self) -> None:
        self.assertEqual(extract_output_text({"output": "not-a-list"}), "")

    def test_ignores_malformed_content_collection(self) -> None:
        payload = {"output": [{"type": "message", "content": "not-a-list"}]}
        self.assertEqual(extract_output_text(payload), "")

    def test_ignores_non_string_text(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": {"value": "no"}}],
                }
            ]
        }
        self.assertEqual(extract_output_text(payload), "")


if __name__ == "__main__":
    unittest.main()
