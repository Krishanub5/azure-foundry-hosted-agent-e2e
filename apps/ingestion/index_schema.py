"""Azure AI Search index definition."""

from __future__ import annotations

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)


def build_index(name: str, vector_dimensions: int) -> SearchIndex:
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="en.microsoft",
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
            ),
            SimpleField(
                name="source_uri",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True,
            ),
            SimpleField(
                name="chunk_number",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True,
            ),
            SimpleField(
                name="content_hash",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=vector_dimensions,
                vector_search_profile_name="vector-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw",
                )
            ],
        ),
    )
