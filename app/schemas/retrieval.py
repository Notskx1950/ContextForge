from typing import Any

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=25)
    strategy: str = "keyword_mock"
    filters: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: int
    title: str
    content: str
    score: float
    source_type: str
    source_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    query: str
    strategy: str
    latency_ms: float
    chunks: list[RetrievedChunk]
