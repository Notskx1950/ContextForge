from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval.retriever_service import RetrieverService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/query", response_model=RetrievalResponse)
def query(request: RetrievalRequest, db: Session = Depends(get_db)) -> RetrievalResponse:
    return RetrieverService(db).retrieve(request)
