GOLDEN_DOCUMENTS = [
    {
        "title": "Async inference design",
        "raw_text": (
            "Async inference uses a worker queue. "
            "Latency increases when queue depth rises or workers are saturated."
        ),
        "source_type": "design_doc",
        "source_uri": "eval://async-inference-design",
        "metadata": {"component": "inference"},
    },
    {
        "title": "Payments retry runbook",
        "raw_text": (
            "Payment retries can fail when idempotency keys expire. "
            "Check the dead letter queue, retry budget, and worker errors."
        ),
        "source_type": "runbook",
        "source_uri": "eval://payments-retry-runbook",
        "metadata": {"component": "payments"},
    },
    {
        "title": "Embedding indexing note",
        "raw_text": (
            "Embeddings are generated asynchronously and indexed into vector storage. "
            "Hybrid retrieval can combine keyword and vector search."
        ),
        "source_type": "design_doc",
        "source_uri": "eval://embedding-indexing-note",
        "metadata": {"component": "retrieval"},
    },
]


GOLDEN_RETRIEVAL_CASES = [
    {
        "query": "async inference latency queue depth",
        "top_k": 3,
        "filters": {"metadata": {"component": "inference"}},
        "expected_titles": ["Async inference design"],
    },
    {
        "query": "payment retry idempotency dead letter queue",
        "top_k": 3,
        "filters": {
            "source_type": "runbook",
            "metadata": {"component": "payments"},
        },
        "expected_titles": ["Payments retry runbook"],
    },
    {
        "query": "embeddings vector storage hybrid retrieval",
        "top_k": 3,
        "filters": {"metadata": {"component": "retrieval"}},
        "expected_titles": ["Embedding indexing note"],
    },
]