import time

from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, RetrievalRun
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievedChunk
from app.services.retrieval.bm25 import bm25_scores, keyword_score
from app.services.retrieval.embeddings import BaseEmbeddingProvider, LocalHashEmbeddingProvider
from app.services.retrieval.reranker import BaseReranker, NoOpReranker
from app.services.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore, VectorDocument

class RetrieverService:
    def __init__(
        self,
        db: Session,
        reranker: BaseReranker | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        vector_store: BaseVectorStore | None = None,
    ) -> None:
        self.db = db
        self.reranker = reranker or NoOpReranker()
        self.embedding_provider = embedding_provider or LocalHashEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        started = time.perf_counter()
        rows = self.db.query(Chunk, Document).join(Document, Chunk.document_id == Document.id).all()
        candidate_rows = [
            (chunk, document)
            for chunk, document in rows
            if self._matches_filters(chunk, document, request)
        ]

        scored: list[RetrievedChunk] = []
        scores = self._score_candidates(request, candidate_rows)

        for (chunk, document), score in zip(candidate_rows, scores, strict=True):
            if score <= 0:
                continue

            metadata = self._combined_metadata(chunk, document)
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    title=document.title,
                    content=chunk.content,
                    score=score,
                    source_type=document.source_type,
                    source_uri=document.source_uri,
                    metadata=metadata,
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

    def _score_candidates(
        self,
        request: RetrievalRequest,
        candidate_rows: list[tuple[Chunk, Document]],
    ) -> list[float]:
        if request.strategy == "keyword_mock":
            return [keyword_score(request.query, chunk.content) for chunk, _ in candidate_rows]

        if request.strategy == "bm25":
            corpus = [chunk.content for chunk, _ in candidate_rows]
            return bm25_scores(request.query, corpus)

        if request.strategy == "vector":
            return self._vector_scores(request.query, candidate_rows)

        if request.strategy == "hybrid":
            corpus = [chunk.content for chunk, _ in candidate_rows]
            bm25 = bm25_scores(request.query, corpus)
            vector = self._vector_scores(request.query, candidate_rows)

            bm25_norm = self._normalize_scores(bm25)
            vector_norm = self._normalize_scores(vector)

            return [
                round((0.55 * bm25_score) + (0.45 * vector_score), 4)
                for bm25_score, vector_score in zip(bm25_norm, vector_norm, strict=True)
            ]

        return [0.0 for _ in candidate_rows]

    def _vector_scores(
        self,
        query: str,
        candidate_rows: list[tuple[Chunk, Document]],
    ) -> list[float]:
        query_embedding = self.embedding_provider.embed_text(query)
        vector_documents = self._to_vector_documents(candidate_rows)
        score_by_chunk_id = self.vector_store.score(query_embedding, vector_documents)

        return [
            score_by_chunk_id.get(chunk.id, 0.0)
            for chunk, _ in candidate_rows
        ]

    def _to_vector_documents(
        self,
        candidate_rows: list[tuple[Chunk, Document]],
    ) -> list[VectorDocument]:
        documents: list[VectorDocument] = []

        for chunk, document in candidate_rows:
            metadata = self._combined_metadata(chunk, document)
            documents.append(
                VectorDocument(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    title=document.title,
                    content=chunk.content,
                    source_type=document.source_type,
                    source_uri=document.source_uri,
                    metadata=metadata,
                    embedding=self.embedding_provider.embed_text(chunk.content),
                )
            )

        return documents

    def _normalize_scores(self, scores: list[float]) -> list[float]:
        positive_scores = [max(score, 0.0) for score in scores]
        max_score = max(positive_scores, default=0.0)

        if max_score == 0:
            return [0.0 for _ in positive_scores]

        return [round(score / max_score, 4) for score in positive_scores]

    def _matches_filters(
        self,
        chunk: Chunk,
        document: Document,
        request: RetrievalRequest,
    ) -> bool:
        filters = request.filters

        if filters.source_type is not None and document.source_type != filters.source_type:
            return False

        if filters.document_id is not None and document.id != filters.document_id:
            return False

        metadata = self._combined_metadata(chunk, document)
        for key, expected_value in filters.metadata.items():
            if metadata.get(key) != expected_value:
                return False

        return True

    def _combined_metadata(self, chunk: Chunk, document: Document) -> dict:
        return {
            **(document.metadata_json or {}),
            **(chunk.metadata_json or {}),
        }