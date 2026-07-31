"""Pure helpers for OpenAI-compatible Responses payloads."""

from __future__ import annotations

from typing import Any


def extract_output_text(payload: dict[str, Any]) -> str:
    """Extract text from an OpenAI-compatible Responses API payload."""
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    parts: list[str] = []
    output = payload.get("output", [])
    if not isinstance(output, list):
        return ""
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content_items = item.get("content", [])
        if not isinstance(content_items, list):
            continue
        for content in content_items:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"}:
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(parts).strip()
