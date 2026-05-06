from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.retrieval import RetrievalRequest
from app.services.retrieval.retriever_service import RetrieverService


class BaseTool(ABC):
    name: str

    @abstractmethod
    def run(self, input_json: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class SearchDocsTool(BaseTool):
    name = "search_docs"

    def __init__(self, db: Session) -> None:
        self.retriever = RetrieverService(db)

    def run(self, input_json: dict[str, Any]) -> dict[str, Any]:
        response = self.retriever.retrieve(
            RetrievalRequest(
                query=str(input_json.get("query", "")),
                top_k=int(input_json.get("top_k", 5)),
            )
        )
        return {"chunks": [chunk.model_dump() for chunk in response.chunks]}


class GetChunkByIdTool(BaseTool):
    name = "get_chunk_by_id"

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, input_json: dict[str, Any]) -> dict[str, Any]:
        # TODO: Implement direct chunk lookup for precise citations and file-snippet expansion.
        return {"chunk_id": input_json.get("chunk_id"), "status": "not_implemented_mock"}


class DraftIssueTool(BaseTool):
    name = "draft_issue"

    def run(self, input_json: dict[str, Any]) -> dict[str, Any]:
        # TODO: Add optional GitHub issue creation behind explicit human approval.
        return {
            "title": input_json.get("title", "ContextForge draft issue"),
            "body": input_json.get("body", "Review retrieved evidence before filing."),
            "labels": input_json.get("labels", ["ai-draft", "needs-review"]),
        }

# TODO: Add tools for code search, model eval lookup, benchmark log lookup, and AtlasML integration.
