from app.schemas.common import Citation
from app.schemas.generation import ComposedAnswer
from app.schemas.retrieval import RetrievedChunk
from app.services.generation.llm_provider import BaseLLMProvider, get_llm_provider


class GroundedAnswerComposer:
    def __init__(self, llm_provider: BaseLLMProvider | None = None) -> None:
        self.llm_provider = llm_provider or get_llm_provider()

    def compose(
        self,
        *,
        query: str,
        context_chunks: list[RetrievedChunk],
        evidence_score: float,
    ) -> ComposedAnswer:
        if not context_chunks:
            grounded_answer = self.llm_provider.generate_grounded_answer(
                query=query,
                context_chunks=[],
                evidence_score=evidence_score,
            )
            return ComposedAnswer(
                answer=grounded_answer.answer,
                citations=[],
                unsupported_claims=grounded_answer.unsupported_claims,
                generation_metadata={
                    **grounded_answer.metadata,
                    "citation_validation": "no_context",
                    "cited_chunk_count": 0,
                },
            )

        available_citations = {
            chunk.chunk_id: self._build_citation(chunk)
            for chunk in context_chunks
        }

        grounded_answer = self.llm_provider.generate_grounded_answer(
            query=query,
            context_chunks=context_chunks,
            evidence_score=evidence_score,
        )

        valid_cited_ids = [
            chunk_id
            for chunk_id in grounded_answer.cited_chunk_ids
            if chunk_id in available_citations
        ]

        citations = [available_citations[chunk_id] for chunk_id in valid_cited_ids]

        unsupported_claims = list(grounded_answer.unsupported_claims)

        if grounded_answer.cited_chunk_ids and not citations:
            unsupported_claims.append(
                "The generation provider returned citation IDs that were not present in retrieved context."
            )

        if not grounded_answer.cited_chunk_ids:
            unsupported_claims.append(
                "The generation provider returned an answer without citations."
            )

        return ComposedAnswer(
            answer=grounded_answer.answer,
            citations=citations,
            unsupported_claims=unsupported_claims,
            generation_metadata={
                **grounded_answer.metadata,
                "citation_validation": "passed" if citations else "failed",
                "requested_cited_chunk_ids": grounded_answer.cited_chunk_ids,
                "valid_cited_chunk_ids": valid_cited_ids,
                "cited_chunk_count": len(citations),
                "confidence": grounded_answer.confidence,
            },
        )

    def _build_citation(self, chunk: RetrievedChunk) -> Citation:
        return Citation(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            source_type=chunk.source_type,
            source_uri=chunk.source_uri,
            score=chunk.score,
            content_preview=chunk.content[:240],
        )