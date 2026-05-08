import hashlib
import math
import re
from abc import ABC, abstractmethod

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")

SYNONYM_MAP = {
    "slow": "latency",
    "slowness": "latency",
    "delayed": "latency",
    "delay": "latency",
    "overloaded": "saturated",
    "load": "queue",
}


class BaseEmbeddingProvider(ABC):
    dimension: int

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class LocalHashEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic local embedding provider for tests and local demos.

    This is not a real semantic embedding model. It is a dependency-free vectorizer
    that makes vector retrieval testable before adding OpenAI, BGE, Voyage, etc.
    """

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        buckets = [0.0] * self.dimension

        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = digest[0] % self.dimension
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            buckets[bucket] += sign

        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [round(value / norm, 6) for value in buckets]

    def _tokens(self, text: str) -> list[str]:
        raw_tokens = [token.lower() for token in TOKEN_RE.findall(text)]
        expanded: list[str] = []

        for token in raw_tokens:
            expanded.append(token)
            synonym = SYNONYM_MAP.get(token)
            if synonym:
                expanded.append(synonym)

        return expanded


class MockEmbeddingProvider(LocalHashEmbeddingProvider):
    """Backward-compatible alias for the local deterministic provider."""