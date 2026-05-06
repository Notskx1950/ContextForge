from app.db.session import SessionLocal, init_db
from app.schemas.documents import IngestTextRequest
from app.services.ingestion.ingestion_service import IngestionService

DEMO_DOCS = [
    {
        "title": "Async inference design",
        "source_type": "design_doc",
        "raw_text": "Async inference accepts jobs through an API, stores immutable model version references, and executes work through Redis or RQ workers. Latency can increase when queue depth rises, worker concurrency is too low, or large retrieval fanout is enabled.",
        "metadata": {"component": "inference"},
    },
    {
        "title": "Model registry design",
        "source_type": "design_doc",
        "raw_text": "The model registry stores model versions, artifact URIs, metadata, approvals, lineage, and evaluation summaries. Serving systems should read only approved immutable versions.",
        "metadata": {"component": "registry"},
    },
    {
        "title": "Benchmark report",
        "source_type": "benchmark_log",
        "raw_text": "The latest benchmark showed p95 latency increasing after retrieval fanout changed from 4 to 16. Queue wait time contributed more than model execution time.",
        "metadata": {"component": "evaluation"},
    },
    {
        "title": "Worker queue runbook",
        "source_type": "runbook",
        "raw_text": "If an eval job fails, check worker health, queue depth, Redis connectivity, dataset availability, and whether the model version was approved before retrying.",
        "metadata": {"component": "workers"},
    },
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        service = IngestionService(db)
        for item in DEMO_DOCS:
            response = service.ingest_text(IngestTextRequest(**item))
            print(f"ingested document_id={response.document_id} chunks={response.chunk_count} title={item['title']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
