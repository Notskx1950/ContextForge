from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.services.agent.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/query", response_model=AgentQueryResponse)
def query(request: AgentQueryRequest, db: Session = Depends(get_db)) -> AgentQueryResponse:
    return AgentService(db).query(request)
