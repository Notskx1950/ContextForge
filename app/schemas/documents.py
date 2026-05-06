from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str
    raw_text: str
    source_type: str = "text"
    source_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestTextRequest(DocumentCreate):
    pass


class IngestTextResponse(BaseModel):
    document_id: int
    chunk_count: int


class ChunkRead(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: int
    title: str
    source_type: str
    source_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    chunks: list[ChunkRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
