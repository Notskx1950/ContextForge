import time

from sqlalchemy.orm import Session

from app.db.models import Document, EvalRun
from app.schemas.documents import IngestTextRequest
from app.schemas.evals import EvalRunCreate, EvalRunRead
from app.schemas.retrieval import RetrievalRequest
from app.services.evals.metrics import mean, recall_at_k, reciprocal_rank
from app.services.evals.retrieval_dataset import GOLDEN_DOCUMENTS, GOLDEN_RETRIEVAL_CASES
from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retriever_service import RetrieverService


class EvalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_eval(self, request: EvalRunCreate) -> EvalRunRead:
        started = time.perf_counter()
        self._ensure_golden_documents()

        retriever = RetrieverService(self.db)
        recall_scores: list[float] = []
        reciprocal_ranks: list[float] = []

        for case in GOLDEN_RETRIEVAL_CASES:
            response = retriever.retrieve(
                RetrievalRequest(
                    query=case["query"],
                    top_k=case["top_k"],
                    strategy="bm25",
                    filters=case["filters"],
                )
            )
            retrieved_titles = [chunk.title for chunk in response.chunks]
            expected_titles = case["expected_titles"]

            recall_scores.append(
                recall_at_k(
                    expected_items=expected_titles,
                    retrieved_items=retrieved_titles,
                    k=case["top_k"],
                )
            )
            reciprocal_ranks.append(
                reciprocal_rank(
                    expected_items=expected_titles,
                    retrieved_items=retrieved_titles,
                )
            )

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics = {
            "query_count": len(GOLDEN_RETRIEVAL_CASES),
            "recall_at_3": round(mean(recall_scores), 4),
            "mrr": round(mean(reciprocal_ranks), 4),
            "latency_ms": latency_ms,
        }

        run = EvalRun(name=request.name, dataset_name=request.dataset_name, metrics_json=metrics)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        return EvalRunRead(
            id=run.id,
            name=run.name,
            dataset_name=run.dataset_name,
            metrics=run.metrics_json,
            created_at=run.created_at,
        )

    def _ensure_golden_documents(self) -> None:
        ingestion_service = IngestionService(self.db)

        for document in GOLDEN_DOCUMENTS:
            existing = (
                self.db.query(Document)
                .filter(Document.source_uri == document["source_uri"])
                .first()
            )
            if existing is not None:
                continue

            ingestion_service.ingest_text(
                IngestTextRequest(
                    title=document["title"],
                    raw_text=document["raw_text"],
                    source_type=document["source_type"],
                    source_uri=document["source_uri"],
                    metadata=document["metadata"],
                )
            )