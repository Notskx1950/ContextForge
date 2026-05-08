from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

"""Duplicate Policy:
- skip: If a document with the same title and source_uri already exists, skip ingestion.
- replace: If a document with the same title and source_uri already exists, delete old document and chunks, replace it with the new document.
- version: If a document with the same title and source_uri already exists, keep old document and chunks, create a new document with the same title and source_uri, and record versioned_from_document_id in metadata."""
DuplicatePolicy = Literal["skip", "replace", "version"]

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
    action: str = "created"

class IngestMarkdownRequest(DocumentCreate):
    """Ingest a markdown document from raw text."""
    duplicate_policy: DuplicatePolicy = "skip"


class IngestMarkdownFileRequest(BaseModel):
    """Ingest a markdown document from a file path."""
    path: str
    duplicate_policy: DuplicatePolicy = "skip"
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestMarkdownDirectoryRequest(BaseModel):
    """Ingest all markdown documents from a directory."""
    root_dir: str
    recursive: bool = True
    duplicate_policy: DuplicatePolicy = "skip"
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestDocumentResult(BaseModel):
    title: str
    source_uri: str | None = None
    document_id: int
    chunk_count: int
    action: str


class IngestMarkdownDirectoryResponse(BaseModel):
    root_dir: str
    total_files: int
    created: int
    skipped: int
    replaced: int
    versioned: int
    documents: list[IngestDocumentResult] = Field(default_factory=list)


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
