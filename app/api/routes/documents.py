from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.models import Document
from app.db.session import get_db
from app.schemas.documents import (
    ChunkRead,
    DocumentRead,
    IngestMarkdownDirectoryRequest,
    IngestMarkdownDirectoryResponse,
    IngestMarkdownFileRequest,
    IngestMarkdownRequest,
    IngestTextRequest,
    IngestTextResponse,
)
from app.services.ingestion.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest-text", response_model=IngestTextResponse)
def ingest_text(request: IngestTextRequest, db: Session = Depends(get_db)) -> IngestTextResponse:
    return IngestionService(db).ingest_text(request)

@router.post("/ingest-markdown", response_model=IngestTextResponse)
def ingest_markdown(
    request: IngestMarkdownRequest,
    db: Session = Depends(get_db),
) -> IngestTextResponse:
    return IngestionService(db).ingest_markdown(request)


@router.post("/ingest-markdown-file", response_model=IngestTextResponse)
def ingest_markdown_file(
    request: IngestMarkdownFileRequest,
    db: Session = Depends(get_db),
) -> IngestTextResponse:
    return IngestionService(db).ingest_markdown_file(request)


@router.post("/ingest-markdown-directory", response_model=IngestMarkdownDirectoryResponse)
def ingest_markdown_directory(
    request: IngestMarkdownDirectoryRequest,
    db: Session = Depends(get_db),
) -> IngestMarkdownDirectoryResponse:
    return IngestionService(db).ingest_markdown_directory(request)

@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentRead:
    document = (
        db.query(Document)
        .options(selectinload(Document.chunks))
        .filter(Document.id == document_id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = [
        ChunkRead(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            metadata=chunk.metadata_json or {},
            embedding_id=chunk.embedding_id,
            created_at=chunk.created_at,
        )
        for chunk in document.chunks
    ]
    return DocumentRead(
        id=document.id,
        title=document.title,
        source_type=document.source_type,
        source_uri=document.source_uri,
        metadata=document.metadata_json or {},
        created_at=document.created_at,
        chunks=chunks,
    )
