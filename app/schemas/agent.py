from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import Citation


class AgentQueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=25)


class AgentTraceStep(BaseModel):
    node: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class ToolCallRead(BaseModel):
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    status: str = "completed"


class AgentQueryResponse(BaseModel):
    run_id: int
    final_answer: str
    citations: list[Citation]
    trace_steps: list[AgentTraceStep]
    tool_calls: list[ToolCallRead]
    requires_human_approval: bool
