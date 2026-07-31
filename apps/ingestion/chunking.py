"""Deterministic text chunking."""

from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, size: int = 2400, overlap: int = 300) -> list[str]:
    """Split text near paragraph/sentence boundaries with bounded overlap."""
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    if size < 200:
        raise ValueError("Chunk size must be at least 200 characters")
    if overlap < 0 or overlap >= size:
        raise ValueError("Chunk overlap must be non-negative and smaller than chunk size")

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        hard_end = min(start + size, len(cleaned))
        end = hard_end
        if hard_end < len(cleaned):
            candidates = [
                cleaned.rfind("\n\n", start + size // 2, hard_end),
                cleaned.rfind(". ", start + size // 2, hard_end),
                cleaned.rfind(" ", start + size // 2, hard_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (1 if cleaned[boundary : boundary + 2] == ". " else 0)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks
