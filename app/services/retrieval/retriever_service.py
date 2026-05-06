import time

from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, RetrievalRun
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievedChunk
from app.services.retrieval.bm25 import keyword_score
from app.services.retrieval.reranker import BaseReranker, NoOpReranker


class RetrieverService:
    def __init__(self, db: Session, reranker: BaseReranker | None = None) -> None:
        self.db = db
        self.reranker = reranker or NoOpReranker()

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        started = time.perf_counter()
        rows = self.db.query(Chunk, Document).join(Document, Chunk.document_id == Document.id).all()
        scored: list[RetrievedChunk] = []

        for chunk, document in rows:
            # TODO: Add metadata filtering, query rewriting, dense retrieval, pgvector search,
            # hybrid score fusion, and stale-document handling.
            score = keyword_score(request.query, chunk.content)
            if score <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    title=document.title,
                    content=chunk.content,
                    score=score,
                    source_type=document.source_type,
                    source_uri=document.source_uri,
                    metadata=chunk.metadata_json or {},
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        reranked = self.reranker.rerank(request.query, scored)[: request.top_k]
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        self.db.add(
            RetrievalRun(
                query=request.query,
                top_k=request.top_k,
                strategy=request.strategy,
                latency_ms=latency_ms,
            )
        )
        self.db.commit()
        return RetrievalResponse(
            query=request.query,
            strategy=request.strategy,
            latency_ms=latency_ms,
            chunks=reranked,
        )
