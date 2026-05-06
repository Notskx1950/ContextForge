def test_retrieval_returns_relevant_chunk_after_ingestion(client, ingested_document):
    response = client.post(
        "/retrieval/query",
        json={"query": "async inference latency queue", "top_k": 3, "strategy": "keyword_mock"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunks"]
    assert "queue" in body["chunks"][0]["content"].lower()
