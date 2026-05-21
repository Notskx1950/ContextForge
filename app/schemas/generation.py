from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import Citation


ConfidenceLevel = Literal["low", "medium", "high"]


class GroundedAnswer(BaseModel):
    """Structured output produced by an LLM provider."""

    answer: str
    cited_chunk_ids: list[int] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComposedAnswer(BaseModel):
    """Final answer object after citation validation."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    generation_metadata: dict[str, Any] = Field(default_factory=dict)