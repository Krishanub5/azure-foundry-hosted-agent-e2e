"""Cosmos DB conversation persistence using Entra authentication."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential


class ConversationStore:
    def __init__(
        self,
        endpoint: str,
        database_name: str,
        container_name: str,
        managed_identity_client_id: str | None,
        history_limit: int,
    ):
        if managed_identity_client_id:
            self.credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
        else:
            self.credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self.client = CosmosClient(endpoint, credential=self.credential)
        self.container = self.client.get_database_client(database_name).get_container_client(
            container_name
        )
        self.history_limit = history_limit

    def get(self, conversation_id: str) -> dict[str, Any] | None:
        try:
            return self.container.read_item(
                item=conversation_id,
                partition_key=conversation_id,
            )
        except exceptions.CosmosResourceNotFoundError:
            return None

    def previous_response_id(self, conversation_id: str) -> str | None:
        item = self.get(conversation_id)
        value = item.get("previous_response_id") if item else None
        return str(value) if value else None

    def append_exchange(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        response_id: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        item = self.get(conversation_id) or {
            "id": conversation_id,
            "created_at": now,
            "messages": [],
            "schema_version": 1,
        }
        messages = list(item.get("messages", []))
        messages.extend(
            [
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": now,
                    "response_id": None,
                },
                {
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": now,
                    "response_id": response_id,
                },
            ]
        )
        item.update(
            {
                "messages": messages[-self.history_limit :],
                "previous_response_id": response_id,
                "updated_at": now,
            }
        )
        self.container.upsert_item(item)

    def close(self) -> None:
        self.client.close()
        self.credential.close()
