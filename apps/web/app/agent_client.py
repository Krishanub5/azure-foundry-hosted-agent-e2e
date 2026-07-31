"""HTTP client for a Foundry Hosted Agent Responses endpoint."""

from __future__ import annotations

import logging

import httpx

from .identity import TokenProvider
from .response_parser import extract_output_text

logger = logging.getLogger(__name__)


class FoundryAgentClient:
    def __init__(
        self,
        endpoint: str,
        token_provider: TokenProvider,
        timeout_seconds: float = 120,
    ):
        self.endpoint = endpoint
        self.token_provider = token_provider
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds, connect=15),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    def respond(self, message: str, previous_response_id: str | None = None) -> tuple[str, str]:
        body: dict[str, object] = {
            "input": message,
            "store": True,
            "stream": False,
        }
        if previous_response_id:
            body["previous_response_id"] = previous_response_id

        token = self.token_provider.get_token("https://ai.azure.com/.default")
        response = self.client.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        if response.status_code >= 400:
            logger.error(
                "Hosted Agent request failed status=%s request_id=%s",
                response.status_code,
                response.headers.get("x-request-id", "unknown"),
            )
            response.raise_for_status()

        payload = response.json()
        response_id = str(payload.get("id") or "")
        answer = extract_output_text(payload)
        if not response_id or not answer:
            raise RuntimeError("Hosted Agent returned an incomplete Responses payload")
        return response_id, answer

    def close(self) -> None:
        self.client.close()
