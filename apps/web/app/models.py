"""API contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,99}$",
    )

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message cannot be empty or whitespace")
        return normalized


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    response_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    response_id: str
    answer: str


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessage]
