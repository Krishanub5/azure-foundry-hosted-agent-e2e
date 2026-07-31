"""Upload documents, create embeddings, and update the Azure AI Search index."""

from __future__ import annotations

import argparse
import hashlib
import logging
import mimetypes
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.storage.blob import BlobServiceClient, ContentSettings
from chunking import chunk_text
from extractors import extract_pages
from index_schema import build_index
from settings import IngestionSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("enterprise_knowledge_ingestion")
SUPPORTED_SUFFIXES = {".pdf", ".docx", ".md", ".markdown", ".txt"}


def batches(items: list[Any], size: int) -> Iterable[list[Any]]:
    if size < 1:
        raise ValueError("Batch size must be at least 1")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def stable_id(source_uri: str, page_number: int | None, chunk_number: int, text: str) -> str:
    material = f"{source_uri}|{page_number}|{chunk_number}|{text}".encode()
    return hashlib.sha256(material).hexdigest()


def escape_odata(value: str) -> str:
    return value.replace("'", "''")


class DocumentIngestor:
    def __init__(self, settings: IngestionSettings):
        self.settings = settings
        self.credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self.project_client = AIProjectClient(
            endpoint=settings.foundry_project_endpoint,
            credential=self.credential,
        )
        self.openai_client = self.project_client.get_openai_client()
        self.index_client = SearchIndexClient(
            endpoint=settings.search_endpoint,
            credential=self.credential,
        )
        self.search_client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index_name,
            credential=self.credential,
        )
        self.blob_service = BlobServiceClient(
            account_url=settings.storage_blob_endpoint,
            credential=self.credential,
        )
        self.container = self.blob_service.get_container_client(settings.storage_container_name)

    def ensure_resources(self) -> None:
        try:
            self.container.create_container()
        except ResourceExistsError:
            logger.debug("Storage container already exists")
        self.index_client.create_or_update_index(
            build_index(
                self.settings.search_index_name,
                self.settings.vector_dimensions,
            )
        )

    def upload_source(self, path: Path, blob_name: str) -> str:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        blob = self.container.get_blob_client(blob_name)
        with path.open("rb") as handle:
            blob.upload_blob(
                handle,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
        return blob.url

    def delete_existing_source(self, source_uri: str) -> None:
        rows = self.search_client.search(
            search_text="*",
            filter=f"source_uri eq '{escape_odata(source_uri)}'",
            select=["id"],
        )
        documents = [{"id": row["id"]} for row in rows]
        for batch in batches(documents, 1000):
            self.search_client.delete_documents(documents=batch)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for batch in batches(texts, self.settings.embedding_batch_size):
            result = self.openai_client.embeddings.create(
                model=self.settings.embedding_deployment_name,
                input=batch,
            )
            ordered = sorted(result.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
        return vectors

    def ingest_file(self, path: Path, root: Path) -> int:
        blob_name = path.relative_to(root).as_posix()
        source_uri = self.upload_source(path, blob_name)
        pages = extract_pages(path)
        records: list[dict[str, Any]] = []
        texts: list[str] = []

        for page in pages:
            chunks = chunk_text(
                page.text,
                size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )
            for chunk_number, content in enumerate(chunks, start=1):
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                records.append(
                    {
                        "id": stable_id(
                            source_uri,
                            page.page_number,
                            chunk_number,
                            content,
                        ),
                        "content": content,
                        "title": path.name,
                        "source_uri": source_uri,
                        "page_number": page.page_number,
                        "chunk_number": chunk_number,
                        "content_hash": content_hash,
                    }
                )
                texts.append(content)

        if not records:
            logger.warning("No text extracted from %s", path)
            return 0

        self.delete_existing_source(source_uri)
        vectors = self.embed(texts)
        if len(vectors) != len(records):
            raise RuntimeError("Embedding response count did not match document chunk count")
        for record, vector in zip(records, vectors, strict=True):
            record["content_vector"] = vector

        for batch in batches(records, 500):
            result = self.search_client.upload_documents(documents=batch)
            failed = [item for item in result if not item.succeeded]
            if failed:
                raise RuntimeError(f"Azure AI Search rejected {len(failed)} document chunks")
        logger.info("Indexed %s chunks from %s", len(records), path.name)
        return len(records)

    def close(self) -> None:
        for client in (
            self.search_client,
            self.index_client,
            self.openai_client,
            self.project_client,
            self.blob_service,
        ):
            close = getattr(client, "close", None)
            if callable(close):
                close()
        self.credential.close()


def collect_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_SUFFIXES else []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True, help="Document or directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.path.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    root = source if source.is_dir() else source.parent
    files = collect_files(source)
    if not files:
        raise RuntimeError(f"No supported documents found under {source}")

    ingestor = DocumentIngestor(IngestionSettings.from_environment())
    try:
        ingestor.ensure_resources()
        total = sum(ingestor.ingest_file(path, root) for path in files)
        logger.info("Ingestion complete: files=%s chunks=%s", len(files), total)
    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
