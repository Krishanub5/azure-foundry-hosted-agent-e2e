"""Environment-backed web application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


@dataclass(frozen=True, slots=True)
class WebSettings:
    agent_endpoint: str
    cosmos_endpoint: str
    cosmos_database_name: str
    cosmos_container_name: str
    managed_identity_client_id: str | None
    application_insights_connection_string: str | None
    title: str
    history_limit: int
    request_timeout_seconds: float

    @classmethod
    def from_environment(cls) -> WebSettings:
        history_limit = int(os.getenv("HISTORY_LIMIT", "50"))
        request_timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
        if history_limit < 2:
            raise RuntimeError("HISTORY_LIMIT must be at least 2")
        if request_timeout_seconds <= 0:
            raise RuntimeError("REQUEST_TIMEOUT_SECONDS must be greater than 0")

        return cls(
            agent_endpoint=_required("AGENT_ENDPOINT"),
            cosmos_endpoint=_required("COSMOS_ENDPOINT"),
            cosmos_database_name=os.getenv("COSMOS_DATABASE_NAME", "assistant"),
            cosmos_container_name=os.getenv("COSMOS_CONTAINER_NAME", "conversations"),
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID"),
            application_insights_connection_string=os.getenv(
                "APPLICATIONINSIGHTS_CONNECTION_STRING"
            ),
            title=os.getenv("UI_TITLE", "Enterprise Knowledge Assistant"),
            history_limit=history_limit,
            request_timeout_seconds=request_timeout_seconds,
        )
