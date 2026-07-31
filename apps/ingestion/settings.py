"""Environment-backed ingestion settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


@dataclass(frozen=True, slots=True)
class IngestionSettings:
    foundry_project_endpoint: str
    embedding_deployment_name: str
    search_endpoint: str
    search_index_name: str
    storage_blob_endpoint: str
    storage_container_name: str
    vector_dimensions: int
    chunk_size: int
    chunk_overlap: int
    embedding_batch_size: int

    @classmethod
    def from_environment(cls) -> IngestionSettings:
        vector_dimensions = int(os.getenv("VECTOR_DIMENSIONS", "3072"))
        chunk_size = int(os.getenv("CHUNK_SIZE", "2400"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "300"))
        embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))

        if vector_dimensions < 1:
            raise RuntimeError("VECTOR_DIMENSIONS must be at least 1")
        if chunk_size < 200:
            raise RuntimeError("CHUNK_SIZE must be at least 200")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise RuntimeError("CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE")
        if embedding_batch_size < 1:
            raise RuntimeError("EMBEDDING_BATCH_SIZE must be at least 1")

        return cls(
            foundry_project_endpoint=_required("FOUNDRY_PROJECT_ENDPOINT").rstrip("/"),
            embedding_deployment_name=_required("EMBEDDING_DEPLOYMENT_NAME"),
            search_endpoint=_required("SEARCH_ENDPOINT").rstrip("/"),
            search_index_name=os.getenv("SEARCH_INDEX_NAME", "enterprise-knowledge"),
            storage_blob_endpoint=_required("STORAGE_BLOB_ENDPOINT").rstrip("/"),
            storage_container_name=os.getenv("STORAGE_CONTAINER_NAME", "documents"),
            vector_dimensions=vector_dimensions,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_batch_size=embedding_batch_size,
        )
