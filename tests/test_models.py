from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "web"))

from app.models import ChatRequest  # noqa: E402


class ModelTests(unittest.TestCase):
    def test_message_is_trimmed(self) -> None:
        request = ChatRequest(message="  hello  ")
        self.assertEqual(request.message, "hello")

    def test_whitespace_only_message_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ChatRequest(message=" \n ")

    def test_safe_conversation_id_is_accepted(self) -> None:
        request = ChatRequest(message="hello", conversation_id="conv-1234")
        self.assertEqual(request.conversation_id, "conv-1234")

    def test_path_like_conversation_id_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ChatRequest(message="hello", conversation_id="../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
