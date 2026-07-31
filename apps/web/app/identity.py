"""Managed-identity token acquisition with a small in-memory cache."""

from __future__ import annotations

import threading
import time

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential


class TokenProvider:
    def __init__(self, managed_identity_client_id: str | None = None):
        if managed_identity_client_id:
            self.credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
        else:
            self.credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self._token: AccessToken | None = None
        self._lock = threading.Lock()

    def get_token(self, scope: str) -> str:
        with self._lock:
            if self._token and self._token.expires_on > int(time.time()) + 300:
                return self._token.token
            self._token = self.credential.get_token(scope)
            return self._token.token

    def close(self) -> None:
        self.credential.close()
