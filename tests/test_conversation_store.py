from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "web"))

from app.conversation_store import ConversationStore  # noqa: E402


class _Container:
    def __init__(self) -> None:
        self.upserted = None

    def upsert_item(self, item) -> None:
        self.upserted = item


class _Closable:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class ConversationStoreTests(unittest.TestCase):
    def test_append_exchange_updates_history_and_response_pointer(self) -> None:
        store = object.__new__(ConversationStore)
        store.history_limit = 4
        store.container = _Container()
        store.get = lambda _conversation_id: {
            "id": "conversation",
            "messages": [
                {"role": "user", "content": "old-1"},
                {"role": "assistant", "content": "old-2"},
                {"role": "user", "content": "old-3"},
            ],
        }

        store.append_exchange("conversation", "new question", "new answer", "resp-9")

        saved = store.container.upserted
        self.assertEqual(len(saved["messages"]), 4)
        self.assertEqual(saved["messages"][-2]["content"], "new question")
        self.assertEqual(saved["messages"][-1]["content"], "new answer")
        self.assertEqual(saved["previous_response_id"], "resp-9")

    def test_previous_response_id_is_normalized(self) -> None:
        store = object.__new__(ConversationStore)
        store.get = lambda _conversation_id: {"previous_response_id": 42}
        self.assertEqual(store.previous_response_id("conversation"), "42")

    def test_close_releases_client_and_credential(self) -> None:
        store = object.__new__(ConversationStore)
        store.client = _Closable()
        store.credential = _Closable()
        store.close()
        self.assertTrue(store.client.closed)
        self.assertTrue(store.credential.closed)


if __name__ == "__main__":
    unittest.main()
