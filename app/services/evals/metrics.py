def retrieval_hit_rate(retrieved_count: int) -> float:
    return 1.0 if retrieved_count > 0 else 0.0


def citation_coverage(citation_count: int, answer_count: int = 1) -> float:
    return min(citation_count / max(answer_count, 1), 1.0)


def unsupported_claim_rate() -> float:
    # TODO: Replace with Ragas faithfulness, answer relevancy, context precision/recall,
    # tool accuracy, and human review labels.
    return 0.0


def recall_at_k(expected_items: list[str], retrieved_items: list[str], k: int) -> float:
    if not expected_items:
        return 0.0

    top_k_items = set(retrieved_items[:k])
    hits = sum(1 for item in expected_items if item in top_k_items)
    return hits / len(expected_items)


def reciprocal_rank(expected_items: list[str], retrieved_items: list[str]) -> float:
    expected = set(expected_items)
    for rank, item in enumerate(retrieved_items, start=1):
        if item in expected:
            return 1 / rank
    return 0.0


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)