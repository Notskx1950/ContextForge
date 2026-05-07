from typing import Any

from pydantic import BaseModel, Field

class RetrievalFilters(BaseModel):
    source_type: str | None = None
    document_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=25)
    strategy: str = "keyword_mock"
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
