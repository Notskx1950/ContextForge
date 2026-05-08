from typing import Any, Literal

from pydantic import BaseModel, Field

RetrievalStrategy = Literal["keyword_mock", "bm25", "vector", "hybrid"]

class RetrievalFilters(BaseModel):
    source_type: str | None = None
    document_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=25)
    strategy: RetrievalStrategy = "bm25"
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


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
