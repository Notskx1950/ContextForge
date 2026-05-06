from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evals import EvalRunCreate, EvalRunRead
from app.services.evals.eval_service import EvalService

router = APIRouter(prefix="/evals", tags=["evals"])


@router.post("/run", response_model=EvalRunRead)
def run_eval(request: EvalRunCreate, db: Session = Depends(get_db)) -> EvalRunRead:
    return EvalService(db).run_eval(request)
