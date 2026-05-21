from typing import Any, TypedDict

from app.schemas.agent import AgentTraceStep, ToolCallRead
from app.schemas.common import Citation
from app.schemas.retrieval import RetrievedChunk


class AgentState(TypedDict, total=False):
    user_query: str
    intent: str
    retrieval_plan: list[str]
    retrieved_chunks: list[RetrievedChunk]
    tool_calls: list[ToolCallRead]
    evidence_score: float
    draft_answer: str
    final_answer: str
    citations: list[Citation]
    unsupported_claims: list[str]
    generation_metadata: dict[str, Any]
    trace_steps: list[AgentTraceStep]
    requires_human_approval: bool