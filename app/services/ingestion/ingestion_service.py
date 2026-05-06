from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.schemas.documents import IngestTextRequest, IngestTextResponse
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.document_loader import DocumentLoader


class IngestionService:
    def __init__(self, db: Session, loader: DocumentLoader | None = None) -> None:
        self.db = db
        self.loader = loader or DocumentLoader()

    def ingest_text(self, request: IngestTextRequest) -> IngestTextResponse:
        raw_text = self.loader.load_text(request.raw_text)
        document = Document(
            title=request.title,
            source_type=request.source_type,
            source_uri=request.source_uri,
            raw_text=raw_text,
            metadata_json=request.metadata,
        )
        self.db.add(document)
        self.db.flush()

        chunks = chunk_text(raw_text)
        for index, content in enumerate(chunks):
            self.db.add(
                Chunk(
                    document_id=document.id,
                    content=content,
                    chunk_index=index,
                    token_count=len(content.split()),
                    metadata_json={"chunker": "paragraph_mock", **request.metadata},
                    # TODO: Store embedding IDs once real embedding jobs are enabled.
                    embedding_id=None,
                )
            )
        self.db.commit()
        return IngestTextResponse(document_id=document.id, chunk_count=len(chunks))
