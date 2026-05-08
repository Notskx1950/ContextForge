from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.schemas.documents import (
    IngestDocumentResult,
    IngestMarkdownDirectoryRequest,
    IngestMarkdownDirectoryResponse,
    IngestMarkdownFileRequest,
    IngestMarkdownRequest,
    IngestTextRequest,
    IngestTextResponse,
)
from app.services.ingestion.chunker import ChunkDraft, chunk_markdown, chunk_text
from app.services.ingestion.document_loader import DocumentLoader
from app.services.ingestion.loaders import LoadedDocument


class IngestionService:
    def __init__(self, db: Session, loader: DocumentLoader | None = None) -> None:
        self.db = db
        self.loader = loader or DocumentLoader()

    def ingest_text(self, request: IngestTextRequest) -> IngestTextResponse:
        raw_text = self.loader.load_text(request.raw_text)
        chunks = [
            ChunkDraft(content=content, metadata={"chunker": "paragraph_mock"})
            for content in chunk_text(raw_text)
        ]

        return self._persist_document(
            title=request.title,
            raw_text=raw_text,
            source_type=request.source_type,
            source_uri=request.source_uri,
            metadata=request.metadata,
            chunks=chunks,
            duplicate_policy="version",
        )

    def ingest_markdown(self, request: IngestMarkdownRequest) -> IngestTextResponse:
        raw_text = self.loader.load_text(request.raw_text)
        chunks = chunk_markdown(raw_text)

        return self._persist_document(
            title=request.title,
            raw_text=raw_text,
            source_type=request.source_type,
            source_uri=request.source_uri,
            metadata={**request.metadata, "format": "markdown"},
            chunks=chunks,
            duplicate_policy=request.duplicate_policy,
        )

    def ingest_markdown_file(self, request: IngestMarkdownFileRequest) -> IngestTextResponse:
        loaded = self.loader.load_markdown_file(request.path)

        return self._ingest_loaded_markdown(
            loaded=loaded,
            extra_metadata=request.metadata,
            duplicate_policy=request.duplicate_policy,
        )

    def ingest_markdown_directory(
        self,
        request: IngestMarkdownDirectoryRequest,
    ) -> IngestMarkdownDirectoryResponse:
        loaded_documents = self.loader.load_markdown_directory(
            request.root_dir,
            recursive=request.recursive,
        )

        results: list[IngestDocumentResult] = []

        for loaded in loaded_documents:
            response = self._ingest_loaded_markdown(
                loaded=loaded,
                extra_metadata=request.metadata,
                duplicate_policy=request.duplicate_policy,
            )
            results.append(
                IngestDocumentResult(
                    title=loaded.title,
                    source_uri=loaded.source_uri,
                    document_id=response.document_id,
                    chunk_count=response.chunk_count,
                    action=response.action,
                )
            )

        return IngestMarkdownDirectoryResponse(
            root_dir=request.root_dir,
            total_files=len(results),
            created=sum(1 for item in results if item.action == "created"),
            skipped=sum(1 for item in results if item.action == "skipped"),
            replaced=sum(1 for item in results if item.action == "replaced"),
            versioned=sum(1 for item in results if item.action == "versioned"),
            documents=results,
        )

    def _ingest_loaded_markdown(
        self,
        *,
        loaded: LoadedDocument,
        extra_metadata: dict,
        duplicate_policy: str,
    ) -> IngestTextResponse:
        chunks = chunk_markdown(loaded.raw_text)

        return self._persist_document(
            title=loaded.title,
            raw_text=loaded.raw_text,
            source_type=loaded.source_type,
            source_uri=loaded.source_uri,
            metadata={**loaded.metadata, **extra_metadata},
            chunks=chunks,
            duplicate_policy=duplicate_policy,
        )

    def _persist_document(
        self,
        *,
        title: str,
        raw_text: str,
        source_type: str,
        source_uri: str | None,
        metadata: dict,
        chunks: list[ChunkDraft],
        duplicate_policy: str,
    ) -> IngestTextResponse:
        existing = self._find_existing_document(source_uri)

        if existing is not None and duplicate_policy == "skip":
            return IngestTextResponse(
                document_id=existing.id,
                chunk_count=len(existing.chunks),
                action="skipped",
            )

        action = "created"

        if existing is not None and duplicate_policy == "replace":
            self.db.delete(existing)
            self.db.flush()
            action = "replaced"

        if existing is not None and duplicate_policy == "version":
            metadata = {
                **metadata,
                "versioned_from_document_id": existing.id,
            }
            action = "versioned"

        document = Document(
            title=title,
            source_type=source_type,
            source_uri=source_uri,
            raw_text=raw_text,
            metadata_json=metadata,
        )
        self.db.add(document)
        self.db.flush()

        for index, chunk in enumerate(chunks):
            self.db.add(
                Chunk(
                    document_id=document.id,
                    content=chunk.content,
                    chunk_index=index,
                    token_count=len(chunk.content.split()),
                    metadata_json={**metadata, **chunk.metadata},
                    embedding_id=None,
                )
            )

        self.db.commit()

        return IngestTextResponse(
            document_id=document.id,
            chunk_count=len(chunks),
            action=action,
        )

    def _find_existing_document(self, source_uri: str | None) -> Document | None:
        if source_uri is None:
            return None

        return self.db.query(Document).filter(Document.source_uri == source_uri).first()