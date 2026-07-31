"""Azure AI Search hybrid retrieval used as an Agent Framework function tool."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from settings import AgentSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Evidence:
    source_label: str
    title: str
    source_uri: str
    page_number: int | None
    score: float | None
    passage: str


def normalize_search_results(
    results: list[dict[str, Any]], max_passage_characters: int
) -> list[Evidence]:
    """Convert Azure Search rows to a small, model-safe evidence contract."""
    evidence: list[Evidence] = []
    for row in results:
        title = str(row.get("title") or "Untitled")
        source_uri = str(row.get("source_uri") or "")
        page = row.get("page_number")
        page_number = int(page) if page is not None else None
        label = title if page_number is None else f"{title}#p{page_number}"
        passage = str(row.get("content") or "")[:max_passage_characters]
        raw_score = row.get("@search.score")
        score = float(raw_score) if raw_score is not None else None
        evidence.append(
            Evidence(
                source_label=label,
                title=title,
                source_uri=source_uri,
                page_number=page_number,
                score=score,
                passage=passage,
            )
        )
    return evidence


class KnowledgeSearch:
    """Lazily initialized, keyless clients for embedding and hybrid retrieval."""

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self.project_client = AIProjectClient(
            endpoint=settings.foundry_project_endpoint,
            credential=self.credential,
        )
        self.openai_client = self.project_client.get_openai_client()
        self.search_client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index_name,
            credential=self.credential,
        )

    def search(self, query: str, top_k: int = 5) -> str:
        cleaned_query = " ".join(query.split())
        if not cleaned_query:
            return json.dumps({"query": query, "evidence": [], "warning": "Empty search query"})

        safe_top_k = max(1, min(int(top_k), 8))
        try:
            embedding = (
                self.openai_client.embeddings.create(
                    model=self.settings.embedding_deployment_name,
                    input=[cleaned_query],
                )
                .data[0]
                .embedding
            )

            rows = self.search_client.search(
                search_text=cleaned_query,
                vector_queries=[
                    VectorizedQuery(
                        vector=embedding,
                        k_nearest_neighbors=safe_top_k,
                        fields=self.settings.search_vector_field,
                    )
                ],
                select=["content", "title", "source_uri", "page_number"],
                top=safe_top_k,
            )
            normalized = normalize_search_results(list(rows), self.settings.max_passage_characters)
            return json.dumps(
                {
                    "query": cleaned_query,
                    "evidence": [asdict(item) for item in normalized],
                    "citation_instruction": (
                        "Cite factual claims using each evidence item's source_label in brackets."
                    ),
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            # Do not log the query or credential-bearing client details.
            logger.exception("Enterprise knowledge retrieval failed: %s", type(exc).__name__)
            return json.dumps(
                {
                    "query": cleaned_query,
                    "evidence": [],
                    "warning": "Knowledge retrieval is temporarily unavailable.",
                }
            )
