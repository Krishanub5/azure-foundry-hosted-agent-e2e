from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "apps" / "agent"
sys.modules.pop("settings", None)
sys.path.insert(0, str(AGENT_DIR))
import rag as agent_rag  # noqa: E402

sys.path.pop(0)
sys.modules.pop("settings", None)


class _EmbeddingResponse:
    data = [SimpleNamespace(embedding=[0.1, 0.2], index=0)]


class _Embeddings:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _EmbeddingResponse()


class _SearchClient:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, object]] = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return self.rows


class AgentRagTests(unittest.TestCase):
    def test_normalizes_search_results_and_bounds_passage(self) -> None:
        rows = [
            {
                "title": "Guide.pdf",
                "source_uri": "https://example.invalid/Guide.pdf",
                "page_number": 4,
                "content": "abcdefghij",
                "@search.score": 0.75,
            }
        ]
        result = agent_rag.normalize_search_results(rows, max_passage_characters=5)
        self.assertEqual(result[0].source_label, "Guide.pdf#p4")
        self.assertEqual(result[0].passage, "abcde")
        self.assertEqual(result[0].score, 0.75)

    def test_empty_search_query_does_not_call_services(self) -> None:
        search = object.__new__(agent_rag.KnowledgeSearch)
        search.openai_client = SimpleNamespace(embeddings=_Embeddings())
        search.search_client = _SearchClient([])

        payload = json.loads(search.search(" \n "))

        self.assertEqual(payload["warning"], "Empty search query")
        self.assertEqual(search.openai_client.embeddings.calls, [])
        self.assertEqual(search.search_client.calls, [])

    def test_hybrid_search_contract(self) -> None:
        embeddings = _Embeddings()
        search_client = _SearchClient(
            [
                {
                    "title": "Policy.md",
                    "source_uri": "https://example.invalid/Policy.md",
                    "page_number": None,
                    "content": "Approved evidence.",
                    "@search.score": 1.25,
                }
            ]
        )
        search = object.__new__(agent_rag.KnowledgeSearch)
        search.settings = SimpleNamespace(
            embedding_deployment_name="embedding",
            search_vector_field="content_vector",
            max_passage_characters=3500,
        )
        search.openai_client = SimpleNamespace(embeddings=embeddings)
        search.search_client = search_client

        payload = json.loads(search.search("  travel   policy ", top_k=99))

        self.assertEqual(payload["query"], "travel policy")
        self.assertEqual(payload["evidence"][0]["source_label"], "Policy.md")
        self.assertEqual(embeddings.calls[0]["model"], "embedding")
        self.assertEqual(search_client.calls[0]["top"], 8)
        self.assertEqual(
            search_client.calls[0]["vector_queries"][0].fields,
            "content_vector",
        )

    def test_service_failure_returns_safe_warning(self) -> None:
        class _FailingEmbeddings:
            @staticmethod
            def create(**_kwargs):
                raise RuntimeError("service unavailable")

        search = object.__new__(agent_rag.KnowledgeSearch)
        search.settings = SimpleNamespace(
            embedding_deployment_name="embedding",
            search_vector_field="content_vector",
            max_passage_characters=3500,
        )
        search.openai_client = SimpleNamespace(embeddings=_FailingEmbeddings())
        search.search_client = _SearchClient([])

        with self.assertLogs("rag", level="ERROR"):
            payload = json.loads(search.search("safe query"))

        self.assertEqual(payload["evidence"], [])
        self.assertEqual(payload["warning"], "Knowledge retrieval is temporarily unavailable.")
        self.assertNotIn("service unavailable", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
