def retrieval_hit_rate(retrieved_count: int) -> float:
    return 1.0 if retrieved_count > 0 else 0.0


def citation_coverage(citation_count: int, answer_count: int = 1) -> float:
    return min(citation_count / max(answer_count, 1), 1.0)


def unsupported_claim_rate() -> float:
    # TODO: Replace with Ragas faithfulness, answer relevancy, context precision/recall,
    # tool accuracy, and human review labels.
    return 0.0
