from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "web"))

from app.agent_client import FoundryAgentClient  # noqa: E402


class _TokenProvider:
    def __init__(self) -> None:
        self.scopes: list[str] = []

    def get_token(self, scope: str) -> str:
        self.scopes.append(scope)
        return "test-access-value"


class AgentClientTests(unittest.TestCase):
    def build_client(self, handler) -> tuple[FoundryAgentClient, _TokenProvider]:
        provider = _TokenProvider()
        client = object.__new__(FoundryAgentClient)
        client.endpoint = "https://example.invalid/responses"
        client.token_provider = provider
        client.client = httpx.Client(
            transport=httpx.MockTransport(handler),
            trust_env=False,
        )
        self.addCleanup(client.close)
        return client, provider

    def test_posts_responses_contract_with_identity_token(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["authorization"] = request.headers["Authorization"]
            captured["payload"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "id": "resp-123",
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": "Grounded answer"}],
                        }
                    ],
                },
            )

        client, provider = self.build_client(handler)
        response_id, answer = client.respond("Question", previous_response_id="resp-122")

        self.assertEqual(response_id, "resp-123")
        self.assertEqual(answer, "Grounded answer")
        self.assertEqual(provider.scopes, ["https://ai.azure.com/.default"])
        self.assertEqual(captured["authorization"], "Bearer test-access-value")
        self.assertEqual(
            captured["payload"],
            {
                "input": "Question",
                "store": True,
                "stream": False,
                "previous_response_id": "resp-122",
            },
        )

    def test_raises_for_http_failure(self) -> None:
        client, _ = self.build_client(
            lambda _request: httpx.Response(503, json={"error": "unavailable"})
        )
        with self.assertRaises(httpx.HTTPStatusError):
            client.respond("Question")

    def test_rejects_incomplete_response(self) -> None:
        client, _ = self.build_client(
            lambda _request: httpx.Response(200, json={"id": "resp-123", "output": []})
        )
        with self.assertRaises(RuntimeError):
            client.respond("Question")


if __name__ == "__main__":
    unittest.main()
