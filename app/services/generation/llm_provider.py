from abc import ABC, abstractmethod

from app.core.config import settings
from app.schemas.generation import GroundedAnswer
from app.schemas.retrieval import RetrievedChunk


class BaseLLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate_grounded_answer(
        self,
        *,
        query: str,
        context_chunks: list[RetrievedChunk],
        evidence_score: float,
    ) -> GroundedAnswer:
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    """Deterministic local provider for tests and demos.

    This is not a real language model. It simulates structured grounded generation
    without external API calls.
    """

    provider_name = "mock"
    model_name = "mock-grounded-generator"

    def generate_grounded_answer(
        self,
        *,
        query: str,
        context_chunks: list[RetrievedChunk],
        evidence_score: float,
    ) -> GroundedAnswer:
        if not context_chunks:
            return GroundedAnswer(
                answer="I do not have enough indexed context to answer this yet. Ingest relevant docs first.",
                cited_chunk_ids=[],
                unsupported_claims=[],
                confidence="low",
                metadata={
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "reason": "no_context",
                },
            )

        top_chunks = context_chunks[:3]
        cited_chunk_ids = [chunk.chunk_id for chunk in top_chunks]

        evidence_lines = [
            f"- {chunk.title}: {chunk.content[:180].strip()}"
            for chunk in top_chunks
        ]

        answer = (
            "Grounded answer based on retrieved ContextForge evidence.\n\n"
            f"User question: {query}\n\n"
            "Most relevant evidence:\n"
            + "\n".join(evidence_lines)
            + "\n\n"
            "Interpretation: The answer should be based only on the retrieved chunks above. "
            "Use the attached citations to inspect the original sources."
        )

        confidence = "high" if evidence_score >= 0.65 else "medium" if evidence_score >= 0.25 else "low"

        return GroundedAnswer(
            answer=answer,
            cited_chunk_ids=cited_chunk_ids,
            unsupported_claims=[],
            confidence=confidence,
            metadata={
                "provider": self.provider_name,
                "model": self.model_name,
                "context_chunk_count": len(context_chunks),
                "evidence_score": evidence_score,
            },
        )


def get_llm_provider() -> BaseLLMProvider:
    """Return the configured LLM provider.

    Phase 4 v0.1 intentionally supports only MockLLMProvider so tests remain
    deterministic and do not require external API keys.
    """
    if settings.use_mock_llm or settings.llm_provider == "mock":
        return MockLLMProvider()

    raise NotImplementedError(
        f"LLM provider '{settings.llm_provider}' is not implemented in Phase 4 v0.1."
    )