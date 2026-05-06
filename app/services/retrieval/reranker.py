from abc import ABC, abstractmethod

from app.schemas.retrieval import RetrievedChunk


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        raise NotImplementedError


class NoOpReranker(BaseReranker):
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        # TODO: Add Cohere rerank, BGE cross-encoder, or LLM-based reranking here.
        return chunks
