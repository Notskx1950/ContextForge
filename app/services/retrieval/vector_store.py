import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VectorDocument:
    chunk_id: int
    document_id: int
    title: str
    content: str
    source_type: str
    source_uri: str | None
    metadata: dict[str, Any]
    embedding: list[float]


class BaseVectorStore(ABC):
    @abstractmethod
    def score(
        self,
        query_embedding: list[float],
        documents: list[VectorDocument],
    ) -> dict[int, float]:
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """Dependency-free vector store for local tests.

    This does not persist vectors. It scores candidate chunks in memory.
    Later this interface can be replaced with pgvector, Qdrant, Weaviate, etc.
    """

    def score(
        self,
        query_embedding: list[float],
        documents: list[VectorDocument],
    ) -> dict[int, float]:
        return {
            document.chunk_id: round(
                cosine_similarity(query_embedding, document.embedding),
                6,
            )
            for document in documents
        }


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)