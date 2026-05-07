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


def test_bm25_ranks_most_relevant_chunk_first(client):
    _ingest(
        client,
        title="Async inference design",
        raw_text=(
            "Async inference uses a worker queue. "
            "Latency increases when queue depth rises or workers are saturated."
        ),
        source_type="design_doc",
        metadata={"component": "inference"},
    )
    _ingest(
        client,
        title="Frontend architecture note",
        raw_text=(
            "Frontend architecture uses component rendering, browser caching, "
            "and design system tokens."
        ),
        source_type="design_doc",
        metadata={"component": "frontend"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "async inference latency queue depth",
            "top_k": 3,
            "strategy": "bm25",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["chunks"]
    assert body["chunks"][0]["title"] == "Async inference design"
    assert body["chunks"][0]["score"] > 0


def test_retrieval_filters_by_source_type(client):
    _ingest(
        client,
        title="Inference design doc",
        raw_text="Queue latency can increase when inference workers are saturated.",
        source_type="design_doc",
        metadata={"component": "inference"},
    )
    _ingest(
        client,
        title="Inference runbook",
        raw_text="Queue latency alerts should be debugged by checking worker saturation.",
        source_type="runbook",
        metadata={"component": "inference"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "queue latency worker saturation",
            "top_k": 5,
            "strategy": "bm25",
            "filters": {"source_type": "runbook"},
        },
    )

    assert response.status_code == 200
    chunks = response.json()["chunks"]
    assert chunks
    assert all(chunk["source_type"] == "runbook" for chunk in chunks)
    assert chunks[0]["title"] == "Inference runbook"


def test_retrieval_filters_by_metadata(client):
    _ingest(
        client,
        title="Inference queue note",
        raw_text="Queue latency can increase when inference workers are saturated.",
        source_type="design_doc",
        metadata={"component": "inference"},
    )
    _ingest(
        client,
        title="Payments queue note",
        raw_text="Queue latency can increase when payment retry workers are saturated.",
        source_type="design_doc",
        metadata={"component": "payments"},
    )

    response = client.post(
        "/retrieval/query",
        json={
            "query": "queue latency workers saturated",
            "top_k": 5,
            "strategy": "bm25",
            "filters": {"metadata": {"component": "payments"}},
        },
    )

    assert response.status_code == 200
    chunks = response.json()["chunks"]
    assert chunks
    assert all(chunk["metadata"]["component"] == "payments" for chunk in chunks)
    assert chunks[0]["title"] == "Payments queue note"