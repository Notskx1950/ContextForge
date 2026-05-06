from abc import ABC, abstractmethod

from app.schemas.retrieval import RetrievedChunk


class BaseVectorStore(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """Placeholder vector store adapter.

    TODO: Replace with pgvector, Qdrant, Weaviate, or a DB-backed vector index. The app should
    depend on this interface, not on a specific vendor client.
    """

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        return []
