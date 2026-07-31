"""Environment-backed settings for the Hosted Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


@dataclass(frozen=True, slots=True)
class AgentSettings:
    foundry_project_endpoint: str
    model_deployment_name: str
    embedding_deployment_name: str
    search_endpoint: str
    search_index_name: str
    search_vector_field: str
    max_passage_characters: int

    @classmethod
    def from_environment(cls) -> AgentSettings:
        model = (
            os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            or os.getenv("FOUNDRY_MODEL_NAME")
            or os.getenv("FOUNDRY_MODEL")
        )
        if not model:
            raise RuntimeError(
                "Set AZURE_AI_MODEL_DEPLOYMENT_NAME, FOUNDRY_MODEL_NAME, or FOUNDRY_MODEL"
            )

        max_passage_characters = int(os.getenv("MAX_PASSAGE_CHARACTERS", "3500"))
        if max_passage_characters < 200:
            raise RuntimeError("MAX_PASSAGE_CHARACTERS must be at least 200")

        return cls(
            foundry_project_endpoint=_required("FOUNDRY_PROJECT_ENDPOINT").rstrip("/"),
            model_deployment_name=model,
            embedding_deployment_name=_required("EMBEDDING_DEPLOYMENT_NAME"),
            search_endpoint=_required("SEARCH_ENDPOINT").rstrip("/"),
            search_index_name=os.getenv("SEARCH_INDEX_NAME", "enterprise-knowledge"),
            search_vector_field=os.getenv("SEARCH_VECTOR_FIELD", "content_vector"),
            max_passage_characters=max_passage_characters,
        )
