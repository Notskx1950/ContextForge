from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError


class MockEmbeddingProvider(BaseEmbeddingProvider):
    def embed_text(self, text: str) -> list[float]:
        # TODO: Replace with OpenAI, Voyage, BGE, or another production embedding provider.
        buckets = [0.0] * 8
        for index, char in enumerate(text.lower()):
            buckets[index % len(buckets)] += float(ord(char) % 31)
        norm = sum(abs(value) for value in buckets) or 1.0
        return [round(value / norm, 4) for value in buckets]
