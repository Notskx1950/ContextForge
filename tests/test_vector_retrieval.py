from fastapi.testclient import TestClient


def _ingest(
    client: TestClient,
    *,
    title: str,
    raw_text: str,
    source_type: str = "design_doc",
    metadata: dict | None = None,
) -> dict:
    response = client.post(
        "/documents/ingest-text",
        json={
            "title": title,
            "raw_text": raw_text,
            "source_type": source_type,
            "metadata": metadata or {},
        },
    )
    assert response.status_code == 200
    return response.json()


def test_vector_retrieval_returns_related_chunk(client):
    _ingest(
        client,
        title="Async inference design",
        raw_text=(
            "Async inference latency rises when queue depth increases "
            "and workers become saturated."
        ),
        metadata={"component": "inference"},
    )
    _ingest(
        client,
        title="Frontend rendering note",
        raw_text=(
            "Frontend rendering uses component trees, browser caching, "
            "and design tokens."
        ),
        metadata={"component": "frontend"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "why is inference slow under load",
            "top_k": 3,
            "strategy": "vector",
        },
    )

    assert response.status_code == 200
    chunks = response.json()["chunks"]

    assert chunks
    assert chunks[0]["title"] == "Async inference design"
    assert chunks[0]["score"] > 0


def test_hybrid_retrieval_respects_metadata_filters(client):
    _ingest(
        client,
        title="Inference queue runbook",
        raw_text=(
            "Inference latency rises when queue depth increases. "
            "Check worker saturation and retry pressure."
        ),
        source_type="runbook",
        metadata={"component": "inference"},
    )
    _ingest(
        client,
        title="Payments queue runbook",
        raw_text=(
            "Payment retry queues can grow when idempotency keys expire "
            "and workers retry failed events."
        ),
        source_type="runbook",
        metadata={"component": "payments"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "queue workers retry pressure",
            "top_k": 5,
            "strategy": "hybrid",
            "filters": {
                "metadata": {
                    "component": "payments"
                }
            },
        },
    )

    assert response.status_code == 200
    chunks = response.json()["chunks"]

    assert chunks
    assert all(chunk["metadata"]["component"] == "payments" for chunk in chunks)
    assert chunks[0]["title"] == "Payments queue runbook"


def test_vector_retrieval_returns_empty_when_no_candidates_match_filter(client):
    _ingest(
        client,
        title="Inference runbook",
        raw_text="Queue depth can increase inference latency.",
        metadata={"component": "inference"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "queue latency",
            "top_k": 3,
            "strategy": "vector",
            "filters": {
                "metadata": {
                    "component": "payments"
                }
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["chunks"] == []