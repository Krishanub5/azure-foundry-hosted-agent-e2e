"""FastAPI middle tier and static chat UI."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent_client import FoundryAgentClient
from .conversation_store import ConversationStore
from .identity import TokenProvider
from .models import ChatRequest, ChatResponse, ConversationResponse
from .settings import WebSettings
from .telemetry import configure_telemetry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("enterprise_knowledge_web")
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = WebSettings.from_environment()
    configure_telemetry(settings.application_insights_connection_string)
    token_provider = TokenProvider(settings.managed_identity_client_id)
    app.state.settings = settings
    app.state.token_provider = token_provider
    app.state.agent = FoundryAgentClient(
        settings.agent_endpoint,
        token_provider,
        timeout_seconds=settings.request_timeout_seconds,
    )
    app.state.store = ConversationStore(
        settings.cosmos_endpoint,
        settings.cosmos_database_name,
        settings.cosmos_container_name,
        settings.managed_identity_client_id,
        settings.history_limit,
    )
    yield
    app.state.agent.close()
    app.state.store.close()
    token_provider.close()


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "no-referrer"
    response.headers["content-security-policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    )
    return response


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(request: Request) -> dict[str, str]:
    # A lightweight token call proves the managed identity endpoint is reachable.
    request.app.state.token_provider.get_token("https://ai.azure.com/.default")
    return {"status": "ready"}


@app.get("/api/config")
def config(request: Request) -> dict[str, str]:
    return {"title": request.app.state.settings.title}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    store: ConversationStore = request.app.state.store
    agent: FoundryAgentClient = request.app.state.agent
    try:
        previous_response_id = store.previous_response_id(conversation_id)
        response_id, answer = agent.respond(
            payload.message,
            previous_response_id=previous_response_id,
        )
        store.append_exchange(
            conversation_id,
            user_message=payload.message,
            assistant_message=answer,
            response_id=response_id,
        )
        return ChatResponse(
            conversation_id=conversation_id,
            response_id=response_id,
            answer=answer,
        )
    except httpx.HTTPStatusError as exc:
        status = 503 if exc.response.status_code >= 500 else 502
        raise HTTPException(status_code=status, detail="The agent service request failed") from exc
    except Exception as exc:
        logger.exception("Chat request failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable",
        ) from exc


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, request: Request) -> dict[str, Any]:
    item = request.app.state.store.get(conversation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "conversation_id": conversation_id,
        "messages": item.get("messages", []),
    }
