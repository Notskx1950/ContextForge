from sqlalchemy.orm import Session

from app.db.models import EvalRun
from app.schemas.evals import EvalRunCreate, EvalRunRead
from app.services.evals.metrics import citation_coverage, retrieval_hit_rate, unsupported_claim_rate


class EvalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_eval(self, request: EvalRunCreate) -> EvalRunRead:
        # TODO: Load a real golden dataset and run retrieval/generation/agent regression tests.
        metrics = {
            "retrieval_hit_rate": retrieval_hit_rate(retrieved_count=1),
            "citation_coverage": citation_coverage(citation_count=1),
            "unsupported_claim_rate": unsupported_claim_rate(),
            "latency_ms": 0.0,
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
